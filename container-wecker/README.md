# Container-Wecker – Docker-Anleitung

Dieses Projekt kann als Docker-Container betrieben werden. Nachfolgend finden Sie die wichtigsten Schritte zur Erstellung und zum Start des Containers.

## Voraussetzungen

- Installiertes [Docker](https://www.docker.com/get-started)
- Zugriff auf das Projektverzeichnis

## Docker-Container erstellen

Führen Sie im Projektverzeichnis folgenden Befehl aus, um das Docker-Image zu bauen:

```sh
docker build -t container-wecker .
```

## Docker-Container starten

Starten Sie den Container mit:

```sh
docker run -d --name container-wecker -p 881:881 -v /var/run/docker.sock:/var/run/docker.sock container-wecker
```

- `-d`: Startet den Container im Hintergrund (detached mode)
- `--name`: Gibt dem Container einen Namen
- `-p 881:881`: Verbindet Port 881 des Hosts mit Port 881 im Container (dies ist der Standardport für die Hauptanwendung)
- `-v /var/run/docker.sock:/var/run/docker.sock`: Bindet den Docker-Socket in den Container ein (z.B. für interne Docker-Kommunikation)

## Allgemeine Informationen

- Der Container enthält die Anwendung zur Verwaltung und Benachrichtigung für die Container-Abholung.
- Konfigurationsdateien können im Projektverzeichnis angepasst werden.
- Logs können mit folgendem Befehl angezeigt werden:

```sh
docker logs container-wecker
```

## Stoppen und Entfernen des Containers

```sh
docker stop container-wecker
docker rm container-wecker
```

## Support

Bei Fragen wenden Sie sich bitte an den Administrator oder prüfen Sie die Dokumentation im Repository.