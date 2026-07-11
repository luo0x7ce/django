pipeline {
    agent any
    
    environment {
        // ==================== 镜像仓库配置 ====================
        HARBOR_URL = 'core.harbor.domain'
        HARBOR_PROJECT = 'library'
        IMAGE_NAME = 'django-server'
        IMAGE_TAG = "${BRANCH_NAME}-${BUILD_NUMBER}-${GIT_COMMIT.take(8)}"
        IMAGE_FULL_NAME = "${HARBOR_URL}/${HARBOR_PROJECT}/${IMAGE_NAME}:${IMAGE_TAG}"
        
        // ==================== Kubernetes 配置 ====================
        K8S_NAMESPACE = 'default'
        K8S_DEPLOYMENT_NAME = 'django-server'
        K8S_CONTAINER_NAME = 'django'
        KUBECONFIG_CREDENTIALS = 'KUBECONFIG_CREDENTIALS'
        DOCKER_BUILDKIT = '1'
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    echo "🏷️ 分支: ${env.BRANCH_NAME}"
                    echo "🔖 提交: ${env.GIT_COMMIT}"
                    echo "📦 镜像: ${env.IMAGE_FULL_NAME}"
                }
            }
        }
        
        stage('Build Docker Image') {
            steps {
                script {
                    sh """
                        docker build -t ${IMAGE_FULL_NAME} .
                        docker tag ${IMAGE_FULL_NAME} ${HARBOR_URL}/${HARBOR_PROJECT}/${IMAGE_NAME}:latest
                    """
                }
            }
        }
        
        stage('Push to Harbor') {
            steps {
                // 使用 Username with password 类型的凭据
                withCredentials([usernamePassword(credentialsId: 'harbor', 
                                                  usernameVariable: 'HARBOR_USER', 
                                                  passwordVariable: 'HARBOR_PWD')]) {
                    sh """
                        echo ${HARBOR_PWD} | docker login ${HARBOR_URL} --username ${HARBOR_USER} --password-stdin
                        docker push ${IMAGE_FULL_NAME}
                        docker push ${HARBOR_URL}/${HARBOR_PROJECT}/${IMAGE_NAME}:latest
                    """
                }
            }
        }
        
        stage('Deploy to Kubernetes') {
            when {
                anyOf { branch 'djangomain'; branch 'django_1'; }
            }
            steps {
               withCredentials([file(credentialsId: "${KUBECONFIG_CREDENTIALS}", variable: 'KUBECONFIG_FILE')]) {
                    sh """
					    export KUBECONFIG="${KUBECONFIG_FILE}"
                        # 替换镜像tag到部署文件，或者直接用yaml中的latest
                        kubectl apply -f k8sconfig/
                       kubectl set image deployment/django-server \
                    django=${IMAGE_FULL_NAME} \
                    -n default
                    """
                }
            }
        }
    }
    
    post {
        success {
            echo "✅ Pipeline 执行成功！"
            echo "镜像地址: ${IMAGE_FULL_NAME}"
        }
        failure {
            echo "❌ Pipeline 执行失败！"
        }
        always {
            sh """
                docker rmi ${IMAGE_FULL_NAME} || true
                docker rmi ${HARBOR_URL}/${HARBOR_PROJECT}/${IMAGE_NAME}:latest || true
                docker system prune -f
            """
        }
    }
}
