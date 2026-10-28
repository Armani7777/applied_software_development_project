pipeline {
  agent any
  options { timestamps() }
  stages {
    stage('Tests') {
      steps {
        sh 'docker run --rm -v "$WORKSPACE":/app -w /app python:3.12-slim sh -c "pip install --no-cache-dir -r requirements.txt && pytest"'
      }
    }
    stage('Docker image') {
      steps {
        sh 'docker build -t quote-page-check:${BUILD_NUMBER} -t quote-page-check:latest .'
      }
    }
    stage('Smoke') {
      steps {
        sh '''
          docker rm -f quote-page-check-smoke >/dev/null 2>&1 || true
          docker run -d --name quote-page-check-smoke -p 8765:8765 quote-page-check:latest
          i=0
          until curl -fsS http://127.0.0.1:8765/ >/dev/null; do
            i=$((i+1))
            if [ "$i" -gt 20 ]; then
              docker logs quote-page-check-smoke
              exit 1
            fi
            sleep 1
          done
          echo page is up
          docker rm -f quote-page-check-smoke
        '''
      }
    }
  }
  post {
    always {
      sh 'docker rm -f quote-page-check-smoke >/dev/null 2>&1 || true'
    }
  }
}
