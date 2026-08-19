pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Setup Environment') {
            steps {
                sh '''
                python3 --version
                which python3

                python3 -m venv .venv
        .venv/bin/python --version
                python3 -m venv .venv
                .venv/bin/python -m pip install --upgrade pip
                .venv/bin/pip install -r requirements.txt
                '''
            }
        }

        stage('Test') {
            steps {
                withCredentials([
                    string(
                        credentialsId: 'ci-database-url',
                        variable: 'DATABASE_URL'
                    ),
                    string(
                     credentialsId: 'ci-secret-key',
                     variable: 'SECRET_KEY'   
                    )
                ]){
                    sh '.venv/bin/pytest'
                }
            }
        }

    }
}