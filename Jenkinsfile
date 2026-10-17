
pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                sh 'docker build -t student-service:latest .'
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                    docker rm -f student-service 2>/dev/null || true
                    docker run -d \
                      --name student-service \
                      --restart unless-stopped \
                      --env-file /home/ubuntu/app/BE-student-service/.env \
                      -p 8000:8000 \
                      student-service:latest
                '''
            }
        }
    }
}
