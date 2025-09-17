FROM golang:alpine

ENV GO111MODULE=on
ENV CGO_ENABLED=0

RUN apk add --no-cache git && \
    git clone https://github.com/awslabs/amazon-ecr-credential-helper.git /amazon-ecr-credential-helper

WORKDIR /amazon-ecr-credential-helper/ecr-login/cli/docker-credential-ecr-login

RUN go build -o /go/bin/docker-credential-ecr-login

WORKDIR /go/bin