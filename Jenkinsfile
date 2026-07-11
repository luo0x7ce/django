pipeline {
    agent {
        kubernetes {
            yaml """
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: jnlp
    image: jenkins/inbound-agent:3383.vc8881d4b_0e76-1
    args: ['\$(JENKINS_SECRET)', '\$(JENKINS_NAME)']
    resources:
      requests:
        memory: "256Mi"
        cpu: "250m"
      limits:
        memory: "512Mi"
        cpu: "500m"
  - name: docker
    image: swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/tsaridas/stremio-docker:latest
    command: ['sleep', 'infinity']
    volumeMounts:
    - name: docker-sock
      mountPath: /var/run/docker.sock
    resources:
      requests:
        memory: "128Mi"
        cpu: "100m"
      limits:
        memory: "256Mi"
        cpu: "200m"
  - name: kubectl
    image: bitnami/kubectl:latest
    command: ['sleep', 'infinity']
    resources:
      requests:
        memory: "128Mi"
        cpu: "100m"
      limits:
        memory: "256Mi"
        cpu: "200m"
  volumes:
  - name: docker-sock
    hostPath:
      path: /var/run/docker.sock
"""
        }
    }

    environment {
        // ==================== 镜像仓库配置 ====================
        HARBOR_URL = 'core.harbor.domain'
        HARBOR_PROJECT = 'library'
        IMAGE_NAME = 'django-server'
        IMAGE_TAG = "${BRANCH_NAME}-${BUILD_NUMBER}-${GIT_COMMIT?.take(8)}"
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
                container('jnlp') {
                    checkout scm
                }
                script {
                    echo "🏷️ 分支: ${env.BRANCH_NAME}"
                    echo "🔖 提交: ${env.GIT_COMMIT}"
                    echo "📦 镜像: ${IMAGE_FULL_NAME}"
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                container('docker') {
                    sh """
                        docker build -t ${IMAGE_FULL_NAME} .
                        docker tag ${IMAGE_FULL_NAME} ${HARBOR_URL}/${HARBOR_PROJECT}/${IMAGE_NAME}:latest
                    """
                }
            }
        }

        stage('Push to Harbor') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'harbor',
                                                  usernameVariable: 'HARBOR_USER',
                                                  passwordVariable: 'HARBOR_PWD')]) {
                    container('docker') {
                        // 安全登录，不泄露密码
                        sh """
                            docker login ${HARBOR_URL} --username ${HARBOR_USER} --password-stdin <<< '${HARBOR_PWD}'
                            docker push ${IMAGE_FULL_NAME}
                            docker push ${HARBOR_URL}/${HARBOR_PROJECT}/${IMAGE_NAME}:latest
                        """
                    }
                }
            }
        }

        stage('Deploy to Kubernetes') {
            when {
                anyOf { branch 'djangomain'; branch 'django_1'; branch 'django_jenkins_pod'; }
            }
            steps {
                withCredentials([file(credentialsId: KUBECONFIG_CREDENTIALS, variable: 'KUBECONFIG_FILE')]) {
                    container('kubectl') {
                        sh """
                            export KUBECONFIG="${KUBECONFIG_FILE}"
                            kubectl apply -f k8sconfig/
                            kubectl set image deployment/${K8S_DEPLOYMENT_NAME} \
                                ${K8S_CONTAINER_NAME}=${IMAGE_FULL_NAME} \
                                -n ${K8S_NAMESPACE}
                            kubectl rollout status deployment/${K8S_DEPLOYMENT_NAME} \
                                -n ${K8S_NAMESPACE} --timeout=5m
                        """
                    }
                }
            }
        }
    }

    post {
        success {
            echo "✅ Pipeline 执行成功！镜像地址: ${IMAGE_FULL_NAME}"
        }
        failure {
            echo "❌ Pipeline 执行失败！"
        }
        always {
            container('docker') {
                sh """
                    docker rmi ${IMAGE_FULL_NAME} || true
                    docker rmi ${HARBOR_URL}/${HARBOR_PROJECT}/${IMAGE_NAME}:latest || true
                    docker system prune -f
                """
            }
        }
    }
}
