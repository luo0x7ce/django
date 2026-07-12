pipeline {
    agent {
        kubernetes {
            yaml """
apiVersion: v1
kind: Pod
spec:
  volumes:
  - name: harbor-ca-volume
    configMap:
       name: harbor-ca
  - name: workspace-volume
    emptyDir: {}
  - name: docker-config
    secret:
      secretName: regcred  # 你需要预先创建一个包含 harbor 认证的 secret
  containers:
  - name: jnlp
    image: jenkins/inbound-agent:3383.vc8881d4b_0e76-1
    args: ['\$(JENKINS_SECRET)', '\$(JENKINS_NAME)']
    volumeMounts:
    - name: workspace-volume
      mountPath: /home/jenkins/agent
  - name: kaniko
    image: core.harbor.domain/library/executor:v1
    command: ['sleep', 'infinity'] 
    tty: true
    volumeMounts:
    - name: workspace-volume
      mountPath: /home/jenkins/agent
    - name: docker-config
      mountPath: /kaniko/.docker
    - name: harbor-ca-volume
      mountPath: /etc/ssl/certs/harbor-ca.crt
      subPath: ca.crt
    - name: harbor-ca-volume
      mountPath: /kaniko/.docker/certs.d/core.harbor.domain/ca.crt
      subPath: ca.crt
    # 可选：添加只读挂载权限，避免证书被意外修改
      readOnly: true
  - name: kubectl
    image: bitnami/kubectl:latest
    command: ['sleep', 'infinity']
    volumeMounts:
    - name: workspace-volume
      mountPath: /home/jenkins/agent
"""
        }
    }

    environment {
        HARBOR_URL = 'core.harbor.domain'
        HARBOR_PROJECT = 'library'
        IMAGE_NAME = 'django-server'
        IMAGE_TAG = "${BRANCH_NAME}-${BUILD_NUMBER}-${GIT_COMMIT?.take(8)}"
        IMAGE_FULL_NAME = "${HARBOR_URL}/${HARBOR_PROJECT}/${IMAGE_NAME}:${IMAGE_TAG}"
        K8S_NAMESPACE = 'default'
        K8S_DEPLOYMENT_NAME = 'django-server'
        K8S_CONTAINER_NAME = 'django'
        KUBECONFIG_CREDENTIALS = 'KUBECONFIG_CREDENTIALS'
    }

    stages {
        stage('Checkout') {
            steps {
                container('jnlp') {
                    checkout scm
                }
            }
        }

        stage('Build & Push with Kaniko') {
            steps {
                container('kaniko') {
                    sh """
                        /kaniko/executor \
                          --context dir:///home/jenkins/agent \
                          --dockerfile /home/jenkins/agent/Dockerfile \
                          --destination ${IMAGE_FULL_NAME} \
                          --destination ${HARBOR_URL}/${HARBOR_PROJECT}/${IMAGE_NAME}:latest \
                          --cache=true \
                          --compressed-caching=false
                    """
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
                            export KUBECONFIG="\${KUBECONFIG_FILE}"
                            kubectl apply -f k8sconfig/
                            kubectl set image deployment/\${K8S_DEPLOYMENT_NAME} \
                                \${K8S_CONTAINER_NAME}=\${IMAGE_FULL_NAME} \
                                -n \${K8S_NAMESPACE}
                            kubectl rollout status deployment/\${K8S_DEPLOYMENT_NAME} \
                                -n \${K8S_NAMESPACE} --timeout=5m
                        """
                    }
                }
            }
        }
    }
}

