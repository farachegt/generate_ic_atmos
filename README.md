> Como visualizar este arquivo: use um visualizador de Markdown no seu editor ou IDE, visualize diretamente pelo GitHub, ou, se você não tiver um visualizador específico, copie e cole o conteúdo em uma destas opções: https://markdownlivepreview.com/, https://markdownlivepreview.dev/ ou https://stackedit.io/

# Generate IC Atmos

Este diretório reúne materiais para preparar dados do ERA5 até a geração dos arquivos "ungribados" do WPS.

## Índice

- [generate_ic_atmos.md](docs/generate_ic_atmos.md)
  Guia principal do projeto. Explica o objetivo do fluxo, os pré-requisitos, como rodar a automação e qual é a estrutura final de saída.

- [instalando_wps.md](docs/instalando_wps.md)
  Guia dedicado à instalação do WPS.

- [tutorial_wps.md](docs/tutorial_wps.md)
  Tutorial conceitual do WPS. Explica o papel da `Vtable`, do `namelist.wps`, do `link_grib.csh` e do `ungrib.exe`.

- [generate_ic_atmos.py](generate_ic_atmos.py)
  Script principal de automação. Executa o fluxo `download ERA5 -> link_grib -> ungrib` e entrega os arquivos finais `ERA5:YYYY-MM-DD_HH` na raiz de `output-dir`.

## Guia rápido

O script baixa os dados do ERA5 para o intervalo especificado por `--start` e `--end`, executa `link_grib.csh`, roda o `ungrib.exe` presentes no diretório do WPS (`--wps-dir`) e entrega os arquivos finais `ERA5:YYYY-MM-DD_HH` na raiz de `output-dir`.

Antes de usar o script, faça os pré-requisitos: configure sua conta do CDS com `~/.cdsapirc`, instale o pacote `cdsapi` e tenha uma instalação funcional do WPS com `link_grib.csh`, `ungrib.exe` e `Vtable.ECMWF`.

Parâmetros obrigatórios de `generate_ic_atmos.py`: `--start`, `--end`, `--output-dir` e `--wps-dir`.

```bash
python generate_ic_atmos.py \
  --start 2026-03-01_00 \
  --end 2026-03-05_21 \
  --output-dir /caminho/para/caso_era5 \
  --wps-dir /caminho/para/WPS
```

## Fluxo sugerido

1. Ler [instalando_wps.md](docs/instalando_wps.md) para preparar o ambiente.
2. Ler [tutorial_wps.md](docs/tutorial_wps.md) para entender o processo manual do WPS.
3. Usar [generate_ic_atmos.md](docs/generate_ic_atmos.md) como guia operacional do projeto.
4. Executar [generate_ic_atmos.py](generate_ic_atmos.py) para automatizar o processo.
