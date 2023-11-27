# Security Scan Pipeline

Este repositório contém uma pipeline de segurança que incorpora testes estáticos e dinâmicos para garantir a segurança do seu aplicativo Python. A pipeline é implementada usando o GitHub Actions e inclui as seguintes etapas:

## 1. Static Application Security Testing (SAST) - AppThreat

O teste de SAST é realizado pelo [AppThreat/sast-scan-action](https://github.com/AppThreat/sast-scan-action). Essa ferramenta analisa o código-fonte estático em busca de possíveis vulnerabilidades de segurança, proporcionando uma visão detalhada do código e sugerindo correções. Neste repositório, o SAST é configurado para analisar código Python.

### Implementação:

```yaml
- name: App Threat(SAST)
  uses: AppThreat/sast-scan-action@master
  with:
    type: "python"
```
## 2. Dynamic Application Security Testing (DAST) - OWASP ZAP

O teste DAST é executado usando o [zaproxy/action-full-scan](https://github.com/zaproxy/action-full-scan). Esta etapa verifica a segurança do aplicativo em tempo de execução, identificando possíveis vulnerabilidades através de solicitações e respostas HTTP. Neste caso, o alvo do scan é um contêiner Docker que executa um aplicativo Flask na porta 5000.

Uma peculiaridade é que a ferramenta do OWASP ZAP, abri issues direto no repositório
 
### Implementação:

```yaml
- name: ZAP Scan(DAST)
  uses: zaproxy/action-full-scan@v0.8.0
  with:
    target: 'http://127.0.0.1:5000'
```
## Executando a Pipeline

Ao enviar alterações para este repositório, a pipeline será acionada automaticamente. Os relatórios de SAST e do DAST são armazenados como artefatos da pipeline.

### Visualizando Relatórios

Os relatórios dos scans na seção "Artifacts" da execução da pipeline. 


