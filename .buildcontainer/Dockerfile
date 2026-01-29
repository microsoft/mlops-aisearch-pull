FROM mcr.microsoft.com/devcontainers/miniconda:3

ARG USERNAME=vscode

USER root

# Install dependencies (Base image has git, curl, jq, sudo)
RUN apt-get update && apt-get install -y build-essential software-properties-common

# Install Azure CLI
RUN curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash && \
    az config set extension.use_dynamic_install=yes_without_prompt && \
    az extension add -n ml

# Setup User (vscode user already exists in devcontainer image)
USER $USERNAME
WORKDIR /home/$USERNAME

COPY requirements.txt .

# Configure Conda and create environment
RUN conda config --add channels conda-forge && \
    conda create -n llm-env python=3.12 -y

# Upgrade pip and build tools
RUN conda run -n llm-env pip install --upgrade pip setuptools wheel

# Install dependencies
RUN conda run -n llm-env pip install -r requirements.txt

# Cleanup and list
RUN conda clean -a -y && \
    conda run -n llm-env pip list

RUN echo "conda activate llm-env" >> /home/$USERNAME/.bashrc

ENV PATH=/opt/conda/envs/llm-env/bin:$PATH

CMD ["conda", "run", "-n", "llm-env", "python", "--version"]