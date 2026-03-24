# Pre-processamento ERA5 ate o ungrib

Este projeto cobre o fluxo abaixo:

1. baixar arquivos GRIB do ERA5;
2. preparar o ambiente do WPS;
3. executar `link_grib.csh`;
4. executar `ungrib.exe`;
5. obter os arquivos intermediarios no formato WPS.

Ele **nao** encapsula o uso do `init_atmosphere`.

## O que o script faz

O arquivo `generate_ic_atmos.py` automatiza estas etapas:

1. solicita ao CDS os campos de pressao e de superficie do ERA5;
2. grava os arquivos `.grib` em um diretorio de download;
3. gera um `namelist.wps` minimo para o `ungrib`;
4. cria um diretorio de trabalho do WPS;
5. coloca a `Vtable` correta no diretorio de trabalho;
6. executa `link_grib.csh` para criar os links `GRIBFILE.*`;
7. executa `ungrib.exe`;
8. move os arquivos finais `ERA5:YYYY-MM-DD_HH` para a raiz de `output-dir`;
9. remove, ao final, os diretorios intermediarios do processo, como `downloads/` e `wps_work/`.

O objetivo e permitir que o usuario rode o fluxo completo, mas tambem consiga entender o que esta acontecendo em cada etapa.

Observacao: o download feito por este script e sempre global. Nao ha suporte a recorte espacial.

## Pre-requisitos

Antes de rodar o script, garanta que voce tem:

- uma conta ativa no Copernicus Climate Data Store;
- um arquivo `~/.cdsapirc` configurado com as credenciais da conta;
  - Para adquirir estas credenciais:
    - Abra o [link do Copernicus](https://cds.climate.copernicus.eu/how-to-api)
    - Logue na sua conta, e em seguida suas credenciais estão disponíveis na seção `1. Setup the CDS Api key`, no padrão:
  
   ```text
   url: https://cds.climate.copernicus.eu/api
   key: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
   ```

- o pacote Python `cdsapi` instalado;
  - Se não tiver, execute o comando `python -m pip install cdsapi>=0.7.7`
- uma instalacao funcional do WPS, com pelo menos:
  - `link_grib.csh`
  - `ungrib.exe`
  - `ungrib/Variable_Tables/Vtable.ECMWF`

## Variaveis baixadas

O script baixa dois grupos de campos do ERA5.

Campos em niveis de pressao:

- `geopotential`
- `relative_humidity`
- `temperature`
- `u_component_of_wind`
- `v_component_of_wind`

Campos de superficie:

- `10m_u_component_of_wind`
- `10m_v_component_of_wind`
- `2m_dewpoint_temperature`
- `2m_temperature`
- `geopotential`
- `land_sea_mask`
- `mean_sea_level_pressure`
- `sea_ice_cover`
- `sea_surface_temperature`
- `skin_temperature`
- `snow_depth`
- `soil_temperature_level_1` a `soil_temperature_level_4`
- `surface_pressure`
- `volumetric_soil_water_layer_1` a `volumetric_soil_water_layer_4`

Esses campos foram escolhidos para casar com o fluxo de `ungrib` usando a `Vtable.ECMWF`.

## Como rodar o script

Exemplo basico:

```bash
python generate_ic_atmos/generate_ic_atmos.py \
  --start 2026-03-01_00 \
  --end 2026-03-05_21 \
  --interval-hours 3 \
  --output-dir /caminho/para/caso_era5 \
  --wps-dir /caminho/para/WPS \
  --prefix ERA5
```

Exemplo reutilizando GRIBs ja baixados:

```bash
python generate_ic_atmos/generate_ic_atmos.py \
  --start 2026-03-01_00 \
  --end 2026-03-05_21 \
  --interval-hours 3 \
  --output-dir /caminho/para/caso_era5 \
  --wps-dir /caminho/para/WPS \
  --prefix ERA5 \
  --skip-download
```

## Parametros principais

- `--start`: data inicial da serie temporal.
- `--end`: data final da serie temporal. O horario final e inclusivo.
- `--interval-hours`: frequencia horária dos arquivos.
- `--output-dir`: diretorio raiz da execucao.
- `--wps-dir`: raiz de uma instalacao do WPS.
- `--prefix`: prefixo dos arquivos gerados pelo `ungrib`.
- `--grid`: resolucao do download no CDS.
- `--pressure-levels`: lista de niveis de pressao separados por virgula.
- `--download-dir`: permite separar o diretorio de GRIBs do restante do caso.
- `--wps-workdir`: permite escolher explicitamente o diretorio de trabalho do WPS.
- `--skip-download`: nao baixa novamente arquivos existentes.
- `--overwrite-downloads`: sobrescreve os GRIBs locais.
- `--link-grib`, `--ungrib-exe`, `--vtable`: permitem apontar para caminhos especificos quando a estrutura do WPS nao esta no padrao esperado.

## Estrutura de saida

Ao final da execucao, os arquivos finais do `ungrib` ficam armazenados diretamente na raiz de `output-dir`.

Se `output-dir` estava vazio antes da execucao e a configuracao padrao foi usada, o resultado final fica assim:

```text
output-dir/
|-- ERA5:YYYY-MM-DD_HH
|-- ERA5:YYYY-MM-DD_HH
|-- ERA5:YYYY-MM-DD_HH
`-- ...
```

Esses arquivos `ERA5:YYYY-MM-DD_HH` sao os produtos finais deste processo, isto e, os arquivos "ungribados".

Durante a execucao, o script pode montar temporariamente uma estrutura como esta:

```text
output-dir/
|-- downloads/
|   |-- era5_pl_YYYYMMDD_HHMM.grib
|   `-- era5_sfc_YYYYMMDD_HHMM.grib
`-- wps_work/
    |-- namelist.wps
    |-- Vtable
    |-- GRIBFILE.AAA
    |-- GRIBFILE.AAB
    |-- ungrib.log
    `-- ERA5:YYYY-MM-DD_HH
```

Ao terminar, o script move os arquivos finais para `output-dir` e remove os subdiretorios intermediarios usados no processo, como `downloads/` e `wps_work/`.

Observacoes:

- arquivos que ja existiam em `output-dir` antes da execucao sao preservados;
- se ja existir em `output-dir` um arquivo com o mesmo nome de uma saida final, o script interrompe a execucao com erro para evitar sobrescrita acidental;
- a remocao automatica atua sobre os diretorios intermediarios configurados dentro de `output-dir`;
- se `--download-dir` ou `--wps-workdir` apontarem para fora de `output-dir`, esses caminhos externos nao sao removidos automaticamente.

## O que acontece em cada etapa

O detalhamento conceitual do fluxo é explicado em [tutorial_wps.md](tutorial_wps.md).

Nesse documento separado você encontra:

- o papel do `link_grib.csh` e do `ungrib.exe`;
- a importância da `Vtable.ECMWF`;
- como o `namelist.wps` entra no processo;
- o que acontece em cada uma das etapas, do download até a geração dos arquivos `ERA5:YYYY-MM-DD_HH`.


## Como verificar se deu certo

Sinais de sucesso:

- existem arquivos com o prefixo definido, por exemplo `ERA5:2026-03-01_00`;
- a quantidade de arquivos finais acompanha a quantidade de horarios solicitados.

## Erros comuns

### Erro de autenticacao no CDS

Normalmente indica problema no `~/.cdsapirc` ou falta de permissao para acessar o dataset.

### `ungrib.exe` nao encontra todos os horarios

Quase sempre significa que:

- `start_date` e `end_date` nao batem com os arquivos disponiveis;
- `interval_seconds` nao bate com a cadencia dos GRIBs;
- algum horario esta faltando no diretorio de download.

### `Vtable` errada

Se a tabela nao for a `Vtable.ECMWF` para os dados do ERA5, o `ungrib` pode interpretar campos errados ou simplesmente nao reconhecer parte dos dados.

### Colisao com arquivos finais existentes

Se `output-dir` ja contiver um arquivo com o mesmo nome de uma saida final, por exemplo `ERA5:2026-03-01_00`, o script aborta para evitar sobrescrever um resultado anterior.

## Resumo operacional

Para um caso novo, a receita curta e:

1. configurar `cdsapi` e WPS;
2. rodar `generate_ic_atmos.py` com periodo, frequencia e caminhos corretos;
3. conferir os arquivos `ERA5:YYYY-MM-DD_HH` na raiz de `output-dir`.

Depois disso, o fluxo de pre-processamento ate o `ungrib` esta concluido.
