# Compilar o WPS no Jaci para utilizar somente o `ungrib`

Este documento descreve como compilar o WPS 4.7.0 no cluster Jaci para utilizar o `ungrib.exe`, sem uma instalação prévia do WRF e sem NetCDF. A compilação utiliza GNU Fortran e inclui suporte a arquivos GRIB2.

## 1. Preparar o ambiente

Se outro ambiente de programação estiver carregado, troque-o pelo ambiente GNU. Por exemplo:

```bash
module swap PrgEnv-cray PrgEnv-gnu/8.6.0
```

Se nenhum ambiente de programação estiver carregado, use:

```bash
module load PrgEnv-gnu/8.6.0
```

Confira os módulos e as ferramentas necessárias:

```bash
module list

command -v gcc
command -v gfortran
command -v make
command -v perl
command -v csh
```

Se `gfortran` não estiver disponível, carregue o GCC nativo:

```bash
module load gcc-native/13.2
```

Não é necessário carregar MPI, NetCDF, HDF5, ecCodes, wgrib2, ESMF ou PIO. O `ungrib` é serial, e as bibliotecas necessárias para GRIB2 serão compiladas pelo próprio WPS.

## 2. Obter o WPS

Clone a versão 4.7.0:

```bash
mkdir -p ~/git
cd ~/git

git clone --branch v4.7.0 --depth 1 \
    https://github.com/wrf-model/WPS.git

cd WPS
```

Se o repositório já existir, entre no diretório e limpe uma compilação anterior:

```bash
cd ~/git/WPS
./clean -a
```

## 3. Limpar variáveis de outras instalações

Remova variáveis que possam apontar para instalações externas do WRF, NetCDF ou JasPer:

```bash
unset WRF_DIR
unset NETCDF
unset NETCDFF
unset JASPERLIB
unset JASPERINC
```

## 4. Configurar

Execute:

```bash
./configure --nowrf --build-grib2-libs
```

As opções utilizadas são:

- `--nowrf`: permite compilar o `ungrib` sem uma instalação compilada do WRF;
- `--build-grib2-libs`: compila zlib, libpng e JasPer para habilitar GRIB2.

Quando aparecer a pergunta sobre NetCDF:

```text
** WARNING: No path to NETCDF and environment variable NETCDF not set.
** would you like me to try to fix? [y]
```

responda:

```text
n
```

Na lista de plataformas, selecione:

```text
Linux x86_64, gfortran (serial)
```

No WPS 4.7.0, essa configuração corresponde à opção 1:

```text
Enter selection [1-22] : 1
```

Use a descrição da plataforma como referência, pois a numeração pode mudar em outras versões.

## 5. Compilar

Compile somente o `ungrib` e salve o log:

```bash
cd ~/git/WPS
./compile ungrib > ~/compile_ungrib.log 2>&1
```

Para acompanhar a compilação em outro terminal:

```bash
tail -f ~/compile_ungrib.log
```

## 6. Verificar o resultado

Confirme que o executável foi criado:

```bash
cd ~/git/WPS

test -x ungrib.exe && echo "ungrib compilado com sucesso"
ls -lhL ungrib.exe
file ungrib.exe
```

O diretório principal normalmente contém o seguinte link simbólico:

```text
ungrib.exe -> ungrib/src/ungrib.exe
```

Se o executável não existir, consulte o final do log:

```bash
tail -n 100 ~/compile_ungrib.log
```

Procure principalmente por mensagens como:

```text
cannot find
undefined reference
Interrupt
```

## 7. Executar o `ungrib`

Em uma nova sessão, carregue o mesmo ambiente usado na compilação:

```bash
module load PrgEnv-gnu/8.6.0
cd ~/git/WPS
```

O fluxo básico de execução é:

1. configurar as seções `&share` e `&ungrib` de `namelist.wps`;
2. criar o link `Vtable` para a tabela compatível com os dados meteorológicos;
3. criar os links `GRIBFILE.*` com `link_grib.csh`;
4. executar `./ungrib.exe`;
5. conferir `ungrib.log` e os arquivos intermediários produzidos.

Execute o `ungrib.exe` com um único processo, sem `mpiexec` ou `mpirun`.

## Referências

- [Repositório oficial do WPS](https://github.com/wrf-model/WPS)
- [Guia oficial de compilação do WRF e WPS](https://www2.mmm.ucar.edu/wrf/site/documentation/users_guide/compiling.html)
- [Documentação oficial do WPS](https://www2.mmm.ucar.edu/wrf/site/documentation/users_guide/wps.html)
