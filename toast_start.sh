#!/usr/bin/env bash
python3 ./conversations_service.py &
python3 ./pictures_service.py &
python3 ./collazionare.py &