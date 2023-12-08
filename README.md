# ResumeBot

![Python](https://img.shields.io/badge/python-v3.11-blue.svg)
![Gradio](https://img.shields.io/badge/gradio-v4.7.1-brightgreen.svg)
![OpenAI](https://img.shields.io/badge/OpenAI-v1.3.7-blueviolet.svg)
![AWS](https://img.shields.io/badge/AWS-S3-orange.svg)

ResumeBot is an interactive chatbot that leverages the power of Gradio and OpenAI's ChatGPT to provide a conversational
interface for discussing professional experience and qualifications based on a resume.

## Features

- Interactive chat interface built with Gradio.
- Integration with OpenAI's ChatGPT for natural language processing.
- AWS S3 integration for storing and retrieving conversation logs.
- Customizable prompts based on a company and role using query parameters.

## Installation

To set up ResumeBot, follow these steps:

1. Clone the repository:
   ```bash
   git clone https://github.com/yasp-g/resume-chatbot.git
   ```
2. Navigate to the project directory:
   ```bash
   cd resume-chatbot
   ```
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `resume.txt` file in the `utils` folder with your resume content.

## Usage

To start ResumeBot locally, run the following command:

```bash
python main.py
```

The bot will be available at `http://127.0.0.1:7860/` and a public URL provided by Gradio by default.

To run ResumeBot as a Docker container in an Amazon EC2 instance, use the provided Dockerfile to build the image and
launch the container with the appropriate AWS configuration.

Example Docker run command (replace variables with your AWS setup):

```bash
sudo docker run -d -p 8080:8080 \
    --log-driver=awslogs \
    --log-opt awslogs-region=<AWS_REGION> \
    --log-opt awslogs-group=<LOG_GROUP_NAME> \
    -e ENVIRONMENT="<ENVIRONMENT_NAME>" \
    -e INSTANCE_NAME="<INSTANCE_NAME>" \
    -e LAUNCH_MODE="AWS" \
    <DOCKER_IMAGE_NAME>:<DOCKER_IMAGE_TAG> >> /var/log/script.log
```

Variables explanation:

- `<AWS_REGION>`: AWS region (e.g., "us-east-1").
- `<LOG_GROUP_NAME>`: AWS CloudWatch log group name (e.g., "resume-chatbot-log-group-production").
- `<ENVIRONMENT_NAME>`: Environment name (e.g., "production", "staging", "development").
- `<INSTANCE_NAME>`: Instance name for identification (e.g., "resume-chatbot-1").
- `<DOCKER_IMAGE_NAME>`: Docker image name (e.g., "resume-chatbot", "
  123456789012.dkr.ecr.us-east-1.amazonaws.com/resume-chatbot").
- `<DOCKER_IMAGE_TAG>`: Docker image tag (e.g., "latest").

Replace the placeholders with your actual AWS setup values.

## Environment Variables

The following environment variables are used by ResumeBot:

- `OPENAI_API_KEY`: Your OpenAI API key for accessing ChatGPT. This can be set manually or retrieved by
  the `get_api_key()` function in `aws.py`.
- `S3_BUCKET_NAME`: The name of the AWS S3 bucket where conversation logs will be stored. This can be set manually or
  determined by the `get_bucket_path()` function in `aws.py`.
- `INSTANCE_NAME`: Set to "local" when running the app locally. For AWS deployment, this is set by the Docker run
  command.

AWS credentials (`AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`) are managed by AWS's CLI and are not set directly in
the application. They can also be set manually. For AWS deployment, these are managed by AWS's IAM roles and policies
attached to the EC2 instance.

## Dependencies

- Gradio
- OpenAI
- Boto3

## Contributing

Contributions are welcome! For major changes, please open an issue first to discuss what you would like to change.

## License

This project is open-source and available under the MIT License. Please see the LICENSE file for more details once added
to the repository.

## Authors and Acknowledgment

Created by Jasper Gallagher. Special thanks to the OpenAI team for providing the GPT models and to Gradio (via
HuggingFace) for the interface framework.

## Project Status

This project is currently in development. Features and documentation may be added or improved in the future.

## FAQs

- **Q:** How do I customize the chatbot's prompts?
    - **A:** You can customize the prompts by modifying the `make_system_prompt` function in `config.py`.

## Contact

If you have any questions or feedback, please contact Jasper Gallagher at [GitHub](https://github.com/yasp-g).

## Screenshots

Coming soon!