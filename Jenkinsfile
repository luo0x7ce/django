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
      secretName: regcred
  # 【新增】用于在 Init Container 和 Kaniko 之间共享证书的临时卷
  - name: kaniko-certs
    emptyDir: {}

  initContainers:
  - name: init-certs
    image: busybox:latest
    command: ['sh', '-c', 'mkdir -p /certs/core.harbor.domain && cp /source/ca.crt /certs/core.harbor.domain/ca.crt']
    volumeMounts:
    - name: harbor-ca-volume
      mountPath: /source
      readOnly: true
    - name: kaniko-certs
      mountPath: /certs

  containers:
  - name: jnlp
    image: jenkins/inbound-agent:3383.vc8881d4b_0e76-1
    args: ['\$(JENKINS_SECRET)', '\$(JENKINS_NAME)']
    volumeMounts:
    - name: workspace-volume
      mountPath: /home/jenkins/agent

  - name: kaniko
    image: core.harbor.domain/library/executor:v4
    # 确保使用包含 shell 的镜像，如 debug 版，或者确认 executor:v1 支持 sleep
    command: ['/bin/sleep', 'infinity'] 
    tty: true
    volumeMounts:
    - name: workspace-volume
      mountPath: /home/jenkins/agent
    - name: docker-config
      mountPath: /kaniko/.docker
    # 【关键修改】挂载共享的证书卷到 Kaniko 的证书目录
    - name: kaniko-certs
      mountPath: /kaniko/.docker/certs.d/core.harbor.domain
      readOnly: true
    # 如果需要系统级信任，也可以挂载到 /etc/ssl/certs，但通常 Kaniko 优先读取 .docker/certs.d
    # - name: kaniko-certs
    #   mountPath: /etc/ssl/certs/harbor-ca.crt
    #   subPath: ca.crt

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

