{{/*
    Expand the name of the chart.
*/}}
{{- define "the-deep.name" -}}
    {{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
    Create a default fully qualified app name.
    We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
    If release name contains chart name it will be used as a full name.
    https://kubernetes.io/docs/concepts/overview/working-with-objects/names/#dns-label-names
*/}}
    {{- define "the-deep.fullname" -}}
        {{- if .Values.fullnameOverride }}
            {{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
        {{- else }}
            {{- $name := default .Chart.Name .Values.nameOverride }}
            {{- if contains $name .Release.Name }}
                {{- .Release.Name | trunc 63 | trimSuffix "-" }}
            {{- else }}
                {{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
        {{- end }}
    {{- end }}
{{- end }}

{{/*
    Create chart name and version as used by the chart label.
*/}}
{{- define "the-deep.chart" -}}
    {{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
    Create the name of the service account to use
*/}}
    {{- define "the-deep.serviceAccountName" -}}
        {{- if .Values.serviceAccount.create }}
            {{- default (include "the-deep.fullname" .) .Values.serviceAccount.name }}
        {{- else }}
            {{- default "default" .Values.serviceAccount.name }}
    {{- end }}
{{- end }}

{{/*
    Create the name of the secret to be used by the the-deep
*/}}
{{- define "the-deep.secretname" -}}
    {{- if .Values.secretsName }}
        {{- .Values.secretsName -}}
    {{- else }}
        {{- printf "%s-secret" (include "the-deep.fullname" .) -}}
    {{- end -}}
{{- end -}}