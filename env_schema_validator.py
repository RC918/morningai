#!/usr/bin/env python3
"""
Environment Schema Validator - Validates environment variables and configuration
Implements standardized configuration management with schema validation
"""

import os
import logging
import json
import yaml
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum

class ConfigType(Enum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    URL = "url"
    EMAIL = "email"
    SECRET = "secret"

@dataclass
class ConfigField:
    """Configuration field definition"""
    name: str
    type: ConfigType
    required: bool = True
    default: Any = None
    description: str = ""
    validation_pattern: Optional[str] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    choices: Optional[List[str]] = None

@dataclass
class ValidationResult:
    """Configuration validation result"""
    valid: bool
    errors: List[str]
    warnings: List[str]
    missing_required: List[str]
    invalid_values: List[str]

class EnvSchemaValidator:
    """Validates environment variables against defined schema"""
    
    def __init__(self, schema_file: str = "env_schema.yaml"):
        self.schema_file = schema_file
        self.logger = logging.getLogger(__name__)
        self.schema = self._load_schema()
        
    def _load_schema(self) -> Dict[str, ConfigField]:
        """Load configuration schema from file"""
        try:
            if os.path.exists(self.schema_file):
                with open(self.schema_file, 'r') as f:
                    schema_data = yaml.safe_load(f)
                    
                schema = {}
                for field_name, field_config in schema_data.get('fields', {}).items():
                    schema[field_name] = ConfigField(
                        name=field_name,
                        type=ConfigType(field_config.get('type', 'string')),
                        required=field_config.get('required', True),
                        default=field_config.get('default'),
                        description=field_config.get('description', ''),
                        validation_pattern=field_config.get('pattern'),
                        min_length=field_config.get('min_length'),
                        max_length=field_config.get('max_length'),
                        choices=field_config.get('choices')
                    )
                    
                return schema
            else:
                return self._get_default_schema()
                
        except Exception as e:
            self.logger.error(f"Failed to load schema: {e}")
            return self._get_default_schema()
            
    def _get_default_schema(self) -> Dict[str, ConfigField]:
        """Get default schema for Phase 7 components"""
        return {
            'DATABASE_URL': ConfigField(
                name='DATABASE_URL',
                type=ConfigType.URL,
                required=True,
                description='Database connection URL'
            ),
            'REDIS_URL': ConfigField(
                name='REDIS_URL',
                type=ConfigType.URL,
                required=False,
                default='redis://localhost:6379/0',
                description='Redis connection URL'
            ),
            
            'SUPABASE_URL': ConfigField(
                name='SUPABASE_URL',
                type=ConfigType.URL,
                required=True,
                description='Supabase project URL'
            ),
            'SUPABASE_ANON_KEY': ConfigField(
                name='SUPABASE_ANON_KEY',
                type=ConfigType.SECRET,
                required=True,
                description='Supabase anonymous key'
            ),
            'SUPABASE_SERVICE_ROLE_KEY': ConfigField(
                name='SUPABASE_SERVICE_ROLE_KEY',
                type=ConfigType.SECRET,
                required=True,
                description='Supabase service role key'
            ),
            
            'CLOUDFLARE_API_TOKEN': ConfigField(
                name='CLOUDFLARE_API_TOKEN',
                type=ConfigType.SECRET,
                required=True,
                description='Cloudflare API token'
            ),
            'CLOUDFLARE_ZONE_ID': ConfigField(
                name='CLOUDFLARE_ZONE_ID',
                type=ConfigType.STRING,
                required=True,
                description='Cloudflare zone ID'
            ),
            
            'VERCEL_TOKEN': ConfigField(
                name='VERCEL_TOKEN',
                type=ConfigType.SECRET,
                required=True,
                description='Vercel deployment token'
            ),
            'VERCEL_ORG_ID': ConfigField(
                name='VERCEL_ORG_ID',
                type=ConfigType.STRING,
                required=True,
                description='Vercel organization ID'
            ),
            'VERCEL_PROJECT_ID': ConfigField(
                name='VERCEL_PROJECT_ID',
                type=ConfigType.STRING,
                required=True,
                description='Vercel project ID'
            ),
            
            'RENDER_API_KEY': ConfigField(
                name='RENDER_API_KEY',
                type=ConfigType.SECRET,
                required=True,
                description='Render API key'
            ),
            
            'UPSTASH_REDIS_REST_URL': ConfigField(
                name='UPSTASH_REDIS_REST_URL',
                type=ConfigType.URL,
                required=True,
                description='Upstash Redis REST URL'
            ),
            'UPSTASH_REDIS_REST_TOKEN': ConfigField(
                name='UPSTASH_REDIS_REST_TOKEN',
                type=ConfigType.SECRET,
                required=True,
                description='Upstash Redis REST token'
            ),
            
            'SENTRY_DSN': ConfigField(
                name='SENTRY_DSN',
                type=ConfigType.URL,
                required=True,
                description='Sentry DSN for error tracking'
            ),
            'SENTRY_AUTH_TOKEN': ConfigField(
                name='SENTRY_AUTH_TOKEN',
                type=ConfigType.SECRET,
                required=False,
                description='Sentry authentication token'
            ),
            
            'FLASK_ENV': ConfigField(
                name='FLASK_ENV',
                type=ConfigType.STRING,
                required=False,
                default='development',
                choices=['development', 'staging', 'production'],
                description='Flask environment'
            ),
            'SECRET_KEY': ConfigField(
                name='SECRET_KEY',
                type=ConfigType.SECRET,
                required=True,
                min_length=32,
                description='Application secret key'
            ),
            'PORT': ConfigField(
                name='PORT',
                type=ConfigType.INTEGER,
                required=False,
                default=5000,
                description='Application port'
            ),
            
            'TELEGRAM_BOT_TOKEN': ConfigField(
                name='TELEGRAM_BOT_TOKEN',
                type=ConfigType.SECRET,
                required=False,
                description='Telegram bot token for HITL approvals'
            ),
            'TELEGRAM_ADMIN_CHAT_ID': ConfigField(
                name='TELEGRAM_ADMIN_CHAT_ID',
                type=ConfigType.STRING,
                required=False,
                description='Telegram admin chat ID'
            ),
            
            'PHASE7_ENABLED': ConfigField(
                name='PHASE7_ENABLED',
                type=ConfigType.BOOLEAN,
                required=False,
                default=True,
                description='Enable Phase 7 components'
            ),
            'OPS_AGENT_ENABLED': ConfigField(
                name='OPS_AGENT_ENABLED',
                type=ConfigType.BOOLEAN,
                required=False,
                default=True,
                description='Enable Ops Agent'
            ),
            'GROWTH_STRATEGIST_ENABLED': ConfigField(
                name='GROWTH_STRATEGIST_ENABLED',
                type=ConfigType.BOOLEAN,
                required=False,
                default=True,
                description='Enable Growth Strategist'
            ),
            'PM_AGENT_ENABLED': ConfigField(
                name='PM_AGENT_ENABLED',
                type=ConfigType.BOOLEAN,
                required=False,
                default=True,
                description='Enable PM Agent'
            ),
            'HITL_APPROVAL_ENABLED': ConfigField(
                name='HITL_APPROVAL_ENABLED',
                type=ConfigType.BOOLEAN,
                required=False,
                default=True,
                description='Enable HITL approval system'
            )
        }
        
    def validate_environment(self) -> ValidationResult:
        """Validate current environment against schema"""
        errors = []
        warnings = []
        missing_required = []
        invalid_values = []
        
        for field_name, field_config in self.schema.items():
            value = os.environ.get(field_name)
            
            if field_config.required and not value:
                if field_config.default is not None:
                    warnings.append(f"Using default value for {field_name}")
                else:
                    missing_required.append(field_name)
                    errors.append(f"Required environment variable {field_name} is missing")
                continue
                
            if not value and not field_config.required:
                continue
                
            validation_error = self._validate_field_value(field_config, value)
            if validation_error:
                invalid_values.append(field_name)
                errors.append(f"{field_name}: {validation_error}")
                
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            missing_required=missing_required,
            invalid_values=invalid_values
        )
        
    def _validate_field_value(self, field: ConfigField, value: str) -> Optional[str]:
        """Validate individual field value"""
        try:
            if field.type == ConfigType.INTEGER:
                int(value)
            elif field.type == ConfigType.FLOAT:
                float(value)
            elif field.type == ConfigType.BOOLEAN:
                if value.lower() not in ['true', 'false', '1', '0', 'yes', 'no']:
                    return f"Invalid boolean value: {value}"
            elif field.type == ConfigType.URL:
                if not (value.startswith('http://') or value.startswith('https://')):
                    return f"Invalid URL format: {value}"
            elif field.type == ConfigType.EMAIL:
                if '@' not in value or '.' not in value.split('@')[1]:
                    return f"Invalid email format: {value}"
                    
            if field.min_length and len(value) < field.min_length:
                return f"Value too short (minimum {field.min_length} characters)"
            if field.max_length and len(value) > field.max_length:
                return f"Value too long (maximum {field.max_length} characters)"
                
            if field.choices and value not in field.choices:
                return f"Invalid choice. Must be one of: {', '.join(field.choices)}"
                
            return None
            
        except ValueError as e:
            return f"Invalid {field.type.value} value: {value}"
            
    def generate_env_template(self) -> str:
        """Generate .env template file"""
        template_lines = [
            "# Morning AI Environment Configuration",
            "# Generated by EnvSchemaValidator",
            f"# Generated at: {os.environ.get('TZ', 'UTC')}",
            ""
        ]
        
        categories = {
            'Database': ['DATABASE_URL', 'REDIS_URL'],
            'Cloud Services': ['SUPABASE_URL', 'SUPABASE_ANON_KEY', 'SUPABASE_SERVICE_ROLE_KEY',
                              'CLOUDFLARE_API_TOKEN', 'CLOUDFLARE_ZONE_ID',
                              'VERCEL_TOKEN', 'VERCEL_ORG_ID', 'VERCEL_PROJECT_ID',
                              'RENDER_API_KEY', 'UPSTASH_REDIS_REST_URL', 'UPSTASH_REDIS_REST_TOKEN',
                              'SENTRY_DSN', 'SENTRY_AUTH_TOKEN'],
            'Application': ['FLASK_ENV', 'SECRET_KEY', 'PORT'],
            'Phase 7': ['TELEGRAM_BOT_TOKEN', 'TELEGRAM_ADMIN_CHAT_ID'],
            'Feature Flags': ['PHASE7_ENABLED', 'OPS_AGENT_ENABLED', 'GROWTH_STRATEGIST_ENABLED',
                             'PM_AGENT_ENABLED', 'HITL_APPROVAL_ENABLED']
        }
        
        for category, field_names in categories.items():
            template_lines.append(f"# {category}")
            template_lines.append("")
            
            for field_name in field_names:
                if field_name in self.schema:
                    field = self.schema[field_name]
                    
                    if field.description:
                        template_lines.append(f"# {field.description}")
                        
                    if field.default is not None:
                        template_lines.append(f"{field_name}={field.default}")
                    elif field.type == ConfigType.SECRET:
                        template_lines.append(f"# {field_name}=your-secret-key-here")
                    else:
                        template_lines.append(f"# {field_name}=")
                        
                    template_lines.append("")
                    
        return "\n".join(template_lines)
        
    def create_schema_file(self):
        """Create schema YAML file"""
        schema_data = {
            'version': '1.0',
            'description': 'Morning AI Phase 7 environment schema',
            'fields': {}
        }
        
        for field_name, field in self.schema.items():
            field_data = {
                'type': field.type.value,
                'required': field.required,
                'description': field.description
            }
            
            if field.default is not None:
                field_data['default'] = field.default
            if field.min_length is not None:
                field_data['min_length'] = field.min_length
            if field.max_length is not None:
                field_data['max_length'] = field.max_length
            if field.choices:
                field_data['choices'] = field.choices
                
            schema_data['fields'][field_name] = field_data
            
        with open(self.schema_file, 'w') as f:
            yaml.dump(schema_data, f, default_flow_style=False, indent=2)
            
    def get_config_summary(self) -> Dict:
        """Get configuration summary"""
        validation_result = self.validate_environment()
        
        return {
            'total_fields': len(self.schema),
            'required_fields': len([f for f in self.schema.values() if f.required]),
            'optional_fields': len([f for f in self.schema.values() if not f.required]),
            'validation_status': 'valid' if validation_result.valid else 'invalid',
            'missing_required': len(validation_result.missing_required),
            'invalid_values': len(validation_result.invalid_values),
            'warnings': len(validation_result.warnings)
        }

env_schema_validator = EnvSchemaValidator()
