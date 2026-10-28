.PHONY: build run stop logs test clean

IMAGE_NAME = docker-health-monitor
CONTAINER_NAME = health-monitor
LOG_DIR ?= $(PWD)/logs

build:
	docker build -t $(IMAGE_NAME) .

run:
	mkdir -p "$(LOG_DIR)"
	docker run -d \
		--name $(CONTAINER_NAME) \
		-p 8000:8000 \
		-v "$(LOG_DIR):/app/logs" \
		-v /var/run/docker.sock:/var/run/docker.sock \
		$(IMAGE_NAME)

stop:
	docker stop $(CONTAINER_NAME)
	docker rm $(CONTAINER_NAME)

logs:
	docker logs -f $(CONTAINER_NAME)

test:
	PYTHONPATH=. python -m pytest -v

clean:
	docker rm -f $(CONTAINER_NAME) 2>/dev/null || true