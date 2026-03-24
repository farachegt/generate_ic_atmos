> Como visualizar este arquivo: use um visualizador de Markdown no seu editor ou IDE. Se você não tiver um visualizador específico, copie e cole o conteúdo em uma destas opções: https://markdownlivepreview.com/, https://markdownlivepreview.dev/ ou https://stackedit.io/

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

Observacao: o download feito por este script e sempre global. Nao ha suporte a recorte espacial, e a resolucao horizontal usada no CDS e fixa em `0.25/0.25`.

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

Parametros obrigatorios:

- `--start`: data inicial da serie temporal. Sem valor padrao.
- `--end`: data final da serie temporal. O horario final e inclusivo. Sem valor padrao.
- `--output-dir`: diretorio raiz da execucao. Sem valor padrao.
- `--wps-dir`: raiz de uma instalacao do WPS. Sem valor padrao.

Parametros opcionais:

- `--interval-hours`: frequencia horaria dos arquivos. Valor padrao: `3`.
- `--prefix`: prefixo dos arquivos gerados pelo `ungrib`. Valor padrao: `ERA5`.
- `--pressure-levels`: lista de niveis de pressao separados por virgula. Valor padrao: `10,30,50,70,100,150,200,250,300,350,400,500,600,650,700,750,775,800,825,850,875,900,925,950,975,1000`.
- `--download-dir`: permite separar o diretorio de GRIBs do restante do caso. Valor padrao efetivo: `output-dir/downloads`.
- `--wps-workdir`: permite escolher explicitamente o diretorio de trabalho do WPS. Valor padrao efetivo: `output-dir/wps_work`.
- `--link-grib`: permite informar explicitamente o caminho do `link_grib.csh`. Valor padrao efetivo: `wps-dir/link_grib.csh`.
- `--ungrib-exe`: permite informar explicitamente o caminho do `ungrib.exe`. Valor padrao efetivo: `wps-dir/ungrib.exe`.
- `--vtable`: permite informar explicitamente o caminho da tabela de variaveis. Valor padrao efetivo: `wps-dir/ungrib/Variable_Tables/Vtable.ECMWF`.
- `--skip-download`: nao baixa novamente arquivos existentes. Valor padrao: desabilitado.
- `--overwrite-downloads`: sobrescreve os GRIBs locais. Valor padrao: desabilitado.
- `--keep-intermediate-files`: preserva os arquivos e diretorios intermediarios gerados durante o processo. Valor padrao: desabilitado, ou seja, a limpeza automatica continua ativa apenas sobre os artefatos da execucao corrente.

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

Ao terminar, o script move os arquivos finais para `output-dir` e, por padrao, remove apenas os arquivos e diretorios intermediarios criados pela execucao corrente.

Se a opcao `--keep-intermediate-files` for usada, os diretorios intermediarios e seus arquivos temporarios sao preservados.

Observacoes:

- arquivos que ja existiam em `output-dir` antes da execucao sao preservados;
- outros arquivos preexistentes em `output-dir` e que nao fazem parte desta execucao nao sao removidos pela limpeza automatica;
- se ja existir em `output-dir` um arquivo com o mesmo nome de uma saida final, o script interrompe a execucao com erro para evitar sobrescrita acidental;
- a remocao automatica atua apenas sobre os artefatos conhecidos desta execucao dentro de `output-dir`, a menos que `--keep-intermediate-files` seja informado;
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

## Validacao

Os arquivos finais gerados por este script foram validados contra arquivos de referencia.

As saidas comparadas sao iguais, e essa verificacao foi realizada através de comparação de hash com `md5sum`.
