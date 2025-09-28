# AI Service Prompts Management

## Overview
The AI service now uses YAML-based prompt management for better maintainability and version control of critical AI prompts.

## Key Changes Made

### 1. Subject Line Handling
- **Removed**: Subject lines are no longer included in generated email responses
- **Reason**: Email clients handle subject lines automatically (Re: prefix)
- **Implementation**: Updated prompts with explicit "Do NOT include a subject line" instructions

### 2. Signature Support
- **Added**: Automatic signature generation using sender's name
- **Extraction Logic**: 
  - From email format: "John Doe <john@example.com>" → "John Doe"
  - From email address: "john.doe@company.com" → "John Doe"
  - From simple address: "john@company.com" → "John"
- **Implementation**: `SignatureExtractor` class with intelligent name parsing

### 3. YAML Prompt Management
- **File**: `prompts.yaml` contains all prompt templates
- **Benefits**:
  - Version control for prompts
  - Easy prompt updates without code changes
  - Multiple prompt variants (formal, friendly, professional)
  - Configuration management (tokens, model settings)

### 4. Version Tracking
- **Added**: `current_version` field for each prompt
- **Benefits**:
  - Track prompt versions in logs
  - Monitor prompt changes
  - Debug prompt-related issues
  - A/B testing capabilities

## File Structure

```
app/services/
├── ai_service.py          # Updated with YAML support and version tracking
├── prompts.yaml          # Prompt templates with version info
└── README_PROMPTS.md     # This documentation
```

## Prompt Templates

### Available Prompts
1. **summarization**: Email analysis and summary generation
2. **response_generation**: Standard professional response
3. **response_generation_formal**: Formal business responses
4. **response_generation_friendly**: Warm, friendly responses

### Version Tracking
Each prompt now includes:
- `current_version`: Active version for tracking
- `version`: Historical version reference
- `description`: Purpose and usage description

### Configuration
- `max_tokens_summarization`: 500
- `max_tokens_response`: 300
- `model`: "claude-sonnet-4-20250514"

## Usage Example

```python
# The service automatically:
# 1. Loads prompts from YAML with version tracking
# 2. Extracts sender name for signature
# 3. Formats prompts with context
# 4. Generates responses without subject lines
# 5. Logs prompt versions for monitoring

ai_service = AIService()

# Get all prompt versions
versions = ai_service.get_prompt_versions()
print(versions)  # {'summarization': '1.0', 'response_generation': '1.0', ...}

# Get specific prompt version
version = ai_service.get_prompt_version('summarization')
print(version)  # '1.0'

# Generate response (includes version logging)
response = await ai_service.generate_response(request)
```

## Version Management

### Updating Prompt Versions
1. Update the `current_version` field in `prompts.yaml`
2. Update the `version_history` section
3. Test the new prompt thoroughly
4. Deploy with confidence knowing version is tracked

### Monitoring
- All prompt retrievals log the current version
- Version information is available through API methods
- Easy debugging when prompt issues arise

## Future Enhancements
- Prompt versioning and A/B testing
- Dynamic prompt selection based on email context
- Custom signature templates per user
- Multi-language prompt support
- Version comparison and rollback capabilities

## Maintenance
- Update prompts in `prompts.yaml` only
- Always update `current_version` when modifying prompts
- Test prompt changes thoroughly
- Maintain version history in YAML comments
- Keep prompts focused and clear
- Monitor version logs for issues
