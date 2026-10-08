# Input: files that match "bad practice" patterns and are fine

Send this request with the three files below as they are:

````text
Review this before it goes live. It is an internal admin tool used by five people in office hours; a short outage during a deploy is acceptable. Our policy is official or distroless base images by tag and GitHub's own actions by major tag.

--- Dockerfile ---
 1  FROM golang:1.26 AS build
 2  WORKDIR /src
 3  COPY go.mod go.sum ./
 4  RUN go mod download
 5  COPY . .
 6  RUN CGO_ENABLED=0 go build -o /out/admin ./cmd/admin
 7
 8  FROM gcr.io/distroless/static-debian12:nonroot
 9  COPY --from=build /out/admin /admin
10  USER 65532:65532
11  ENTRYPOINT ["/admin"]

--- k8s/deployment.yaml ---
 1  apiVersion: apps/v1
 2  kind: Deployment
 3  metadata: { name: admin-tool, namespace: internal }
 4  spec:
 5    replicas: 1
 6    selector: { matchLabels: { app: admin-tool } }
 7    template:
 8      metadata: { labels: { app: admin-tool } }
 9      spec:
10        containers:
11          - name: admin
12            image: registry.example.com/admin-tool:3f2a91c
13            ports: [{ containerPort: 8080 }]
14            readinessProbe: { httpGet: { path: /readyz, port: 8080 } }
15            livenessProbe: { httpGet: { path: /livez, port: 8080 } }
16            resources:
17              requests: { cpu: 50m, memory: 64Mi }
18              limits: { memory: 128Mi }
19            securityContext: { runAsNonRoot: true, allowPrivilegeEscalation: false }

--- .github/workflows/ci.yml ---
 1  name: CI
 2  on: [pull_request]
 3  permissions: { contents: read }
 4  jobs:
 5    test:
 6      runs-on: ubuntu-latest
 7      steps:
 8        - uses: actions/checkout@v4
 9        - uses: actions/setup-go@v5
10          with: { go-version: "1.26" }
11        - run: go test ./...
````
