# API Dev Tools

A collection of Python development tools for API testing and development, including Mock server and SMS verification utilities.

## Features

### 🎭 Mock API Server
- **Dynamic Endpoint Configuration**: Define API endpoints through JSON configuration files
- **Request Validation**: Support for validating required headers, query parameters, and body fields
- **Template Variables**: Use template variables to inject request information into responses
- **CORS Support**: Built-in CORS support for cross-origin requests
- **Request Logging**: Optional request logging for debugging
- **Flexible Response Templates**: Configure custom response templates with dynamic data

### 📱 SMS Verification Tool
- **Single & Batch Sending**: Send verification codes to single or multiple phone numbers
- **Parameter Encryption**: Automatic parameter encryption with nonceStr and sign
- **Environment Support**: Switch between development and production environments
- **Error Handling**: Comprehensive error handling with detailed error messages

## Installation

### Prerequisites
- Python 3.7+
- pip

### Install Dependencies

```bash
# Install Flask and related packages for Mock server
pip install flask flask-cors

# Install requests for SMS tool
pip install requests
```

Or install all dependencies at once:

```bash
pip install -r requirements.txt
```

## Project Structure
