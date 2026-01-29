FROM mcr.microsoft.com/devcontainers/python:3.12

ARG USERNAME=vscode

USER root

# Install Azure CLI
RUN curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash && \
    az config set extension.use_dynamic_install=yes_without_prompt

# Setup User
USER $USERNAME
WORKDIR /home/$USERNAME

COPY requirements.txt .

# Create virtual environment and install dependencies
# We use a venv named 'llm-env' to maintain consistency with previous conda setup
RUN python -m venv llm-env && \
    /home/$USERNAME/llm-env/bin/pip install --upgrade pip setuptools wheel && \
    /home/$USERNAME/llm-env/bin/pip install -r requirements.txt

# Configure shell to use the environment
RUN echo "source /home/$USERNAME/llm-env/bin/activate" >> /home/$USERNAME/.bashrc

# Add venv to PATH
ENV PATH="/home/$USERNAME/llm-env/bin:$PATH"

CMD ["python", "--version"]