#!/bin/bash

source ./.env

read -p "Enter the migration message: " user_input

escaped_input=$(echo $user_input | sed 's/"/\\"/g')

docker exec -it tothetop_backend bash -c "alembic revision --autogenerate -m \"$escaped_input\""