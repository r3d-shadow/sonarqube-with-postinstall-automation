### SonarQube Docker Setup with Post-Install Automation

This guide provides instructions on setting up SonarQube using Docker containers. Additionally, it includes a post-install script for automating tasks such as changing passwords, creating projects, generating tokens, and setting up quality gates.

#### Prerequisites
- Docker installed on your system
- Docker Compose installed on your system

#### Usage
1. Ensure Docker is running on your system.
2. Clone the repository and navigate to it.
3. Create a `.env` file with the required environment variables.
4. Create a data folder for PostgreSQL volume.
5. Execute the following command in your terminal:

```bash
docker-compose up -d
```

#### Post-Install Process
Upon running the Docker Compose setup, the `index.py` script will perform the following tasks:
- Change the admin password
- Log in with the new password
- Create projects specified in `config.json`
- Generate new tokens for the projects.
- Set up a quality gate with specified thresholds

## CLI
docker run --rm -it -v $PWD:/work -w /work sonarsource/sonar-scanner-cli:latest bash
