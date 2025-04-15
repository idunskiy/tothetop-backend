#!/bin/bash

source ./.env

docker exec -it tothetop_backend bash -c "alembic upgrade head"