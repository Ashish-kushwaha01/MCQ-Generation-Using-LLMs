from django import forms
from django.core.exceptions import ValidationError
from .models import Test_Upload
import json
from django.utils.text import slugify # Import slugify

class TestUploadForm(forms.ModelForm):
    class Meta:
        model = Test_Upload
        # Only include json_file, json_data, and test_slug in the form fields
        fields = ['json_file', 'json_data', 'test_slug']

    def clean(self):
        cleaned_data = super().clean()
        json_file = cleaned_data.get('json_file')
        json_data_input = cleaned_data.get('json_data') # Renamed to avoid confusion with parsed data

        source_data = None

        # Handle JSON file upload
        if json_file:
            try:
                source_data = json.load(json_file)
            except json.JSONDecodeError:
                self.add_error('json_file', "Invalid JSON format in the uploaded file.")
            except Exception as e:
                self.add_error('json_file', f"Error reading JSON file: {e}")
        
        # Handle direct JSON data input (JSONField)
        elif json_data_input:
            # json_data_input from a JSONField might already be a dict, or a string if manually entered
            if isinstance(json_data_input, str):
                try:
                    source_data = json.loads(json_data_input)
                except json.JSONDecodeError:
                    self.add_error('json_data', "Invalid JSON format in the pasted data.")
            elif isinstance(json_data_input, dict): # If it's already a dict (from JSONField)
                source_data = json_data_input
            else:
                self.add_error('json_data', "Invalid data type for JSON data.")

        # Validation for providing either json_file or json_data, but not both
        # Check if both are provided
        if json_file and json_data_input:
            raise ValidationError("Please provide either a JSON file or paste JSON data, not both.")
        
        # Check if neither is provided. For existing instances, if json_file is not changed,
        # it won't be in cleaned_data, so we check the instance's current json_file.
        if not json_file and not json_data_input:
            if not self.instance.pk or (not self.instance.json_file and not self.instance.json_data):
                raise ValidationError("Please provide either a JSON file or paste JSON data.")

        # Ensure source_data, if present, is a dictionary to prevent TypeError when calling .get()
        if source_data is not None and not isinstance(source_data, dict):
            if json_file:
                self.add_error('json_file', "JSON content must be a dictionary (object), not a list or other type.")
            elif json_data_input:
                self.add_error('json_data', "JSON content must be a dictionary (object), not a list or other type.")
            source_data = None # Invalidate source_data to prevent further processing

        if source_data:
            # Extract data from JSON and populate model instance fields
            # These fields are no longer directly in the form, but we need to set them on the instance
            # for saving.
            self.instance.title = source_data.get('title')
            self.instance.description = source_data.get('description')
            self.instance.subject = source_data.get('subject')
            self.instance.duration = source_data.get('duration')
            
            questions_list = source_data.get('questions')
            if questions_list is None or not isinstance(questions_list, list):
                raise ValidationError("JSON must contain a 'questions' array.")
            
            self.instance.total_questions = len(questions_list)

            # Basic validation for required fields from JSON
            if not self.instance.title:
                self.add_error('json_data', "Title is required and not found in JSON.")
            if not self.instance.description:
                self.add_error('json_data', "Description is required and not found in JSON.")
            if not self.instance.subject:
                self.add_error('json_data', "Subject is required and not found in JSON.")
            if not self.instance.duration:
                self.add_error('json_data', "Duration is required and not found in JSON.")
            
            # Generate test_slug if not provided and title is available
            if not cleaned_data.get('test_slug') and self.instance.title:
                cleaned_data['test_slug'] = slugify(self.instance.title)

        return cleaned_data