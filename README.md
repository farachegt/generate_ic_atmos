# Generate IC Atmos

Este diretório reúne materiais para preparar dados do ERA5 até a geração dos arquivos "ungribados" do WPS.

## Índice

- [generate_ic_atmos.md](generate_ic_atmos.md)
  Guia principal do projeto. Explica o objetivo do fluxo, os pré-requisitos, como rodar a automação e qual é a estrutura final de saída.

- [instalando_wps.md](instalando_wps.md)
  Guia dedicado à instalação do WPS.

- [tutorial_wps.md](tutorial_wps.md)
  Tutorial conceitual do WPS. Explica o papel da `Vtable`, do `namelist.wps`, do `link_grib.csh` e do `ungrib.exe`.

- [generate_ic_atmos.py](generate_ic_atmos.py)
  Script principal de automação. Executa o fluxo `download ERA5 -> link_grib -> ungrib` e entrega os arquivos finais `ERA5:YYYY-MM-DD_HH` na raiz de `output-dir`.

## Fluxo sugerido

1. Ler [instalando_wps.md](instalando_wps.md) para preparar o ambiente.
2. Ler [tutorial_wps.md](tutorial_wps.md) para entender o processo manual do WPS.
3. Usar [generate_ic_atmos.md](generate_ic_atmos.md) como guia operacional do projeto.
4. Executar [generate_ic_atmos.py](generate_ic_atmos.py) para automatizar o processo.
