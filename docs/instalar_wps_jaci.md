# Compilar o WPS no Jaci para utilizar somente o `ungrib`

Este documento descreve o procedimento validado no Jaci para compilar o WPS 4.7.0 somente com o `ungrib.exe`, sem uma instalação prévia do WRF e sem NetCDF. A compilação utiliza o ambiente Cray e inclui suporte a arquivos GRIB2.

## Resultado esperado

Ao final do procedimento, o diretório principal do WPS deve conter:

```text
ungrib.exe -> ungrib/src/ungrib.exe
```

Esta configuração não compila `geogrid.exe`, `metgrid.exe` ou `int2nc.exe`, pois esses programas dependem das bibliotecas de I/O de uma instalação compilada do WRF.

## 1. Preparar o ambiente

Carregue o ambiente de programação Cray:

```bash
module load PrgEnv-cray/8.6.0
module list
```

Se outro `PrgEnv` já estiver carregado, troque-o pelo `PrgEnv-cray` em vez de manter dois ambientes de programação simultaneamente.

Confirme a disponibilidade das ferramentas usadas pela compilação:

```bash
command -v ftn
command -v gcc
command -v make
command -v perl
command -v csh

ftn --version
gcc --version
```

O ambiente virtual Python não é necessário. Ele pode permanecer ativo desde que não substitua os compiladores ou outras ferramentas no `PATH`.

Não é necessário carregar explicitamente os módulos de MPI, NetCDF, HDF5, ecCodes, wgrib2, ESMF ou PIO. O `ungrib` é serial, e as bibliotecas necessárias para GRIB2 serão compiladas internamente.

## 2. Obter o código-fonte

Use uma versão fixa para tornar a instalação reproduzível:

```bash
mkdir -p ~/git
cd ~/git

git clone --branch v4.7.0 --depth 1 \
    https://github.com/wrf-model/WPS.git

cd WPS
```

Se o repositório já existir, apenas entre no diretório correspondente:

```bash
cd ~/git/WPS
```

## 3. Remover configurações externas que não serão usadas

Como somente o `ungrib` será compilado, remova eventuais variáveis herdadas de instalações anteriores:

```bash
unset WRF_DIR
unset NETCDF
unset NETCDFF
unset JASPERLIB
unset JASPERINC
```

## 4. Configurar o WPS

Execute:

```bash
./configure --nowrf --build-grib2-libs
```

As opções têm as seguintes funções:

- `--nowrf`: permite compilar componentes que não dependem das bibliotecas de I/O do WRF;
- `--build-grib2-libs`: compila internamente zlib, libpng e JasPer para habilitar GRIB2.

Quando o programa perguntar sobre a ausência do NetCDF:

```text
** WARNING: No path to NETCDF and environment variable NETCDF not set.
** would you like me to try to fix? [y]
```

responda:

```text
n
```

O resultado esperado inclui:

```text
Will configure for use without NetCDF
Configuring the WPS without a compiled WRF model.
```

Na lista de plataformas, selecione a configuração serial do compilador Cray:

```text
Cray XE/XC CLE/Linux x86_64, Cray compiler (serial)
```

No ambiente em que este procedimento foi validado, ela correspondia à opção `19`:

```text
Enter selection [1-22] : 19
```

O número pode mudar se a versão do WPS ou os compiladores disponíveis forem diferentes. Use a descrição da configuração como referência principal.

## 5. Corrigir o caminho das bibliotecas GRIB2

No Jaci, libpng e JasPer são instaladas em `grib2/lib64`, mas o `configure.wps` gerado pelo WPS 4.7.0 aponta inicialmente somente para `grib2/lib`. Sem a correção, a etapa final de linkedição termina com:

```text
ld: cannot find -ljasper: No such file or directory
```

Abra o arquivo de configuração:

```bash
nano configure.wps
```

Localize a definição original de `COMPRESSION_LIBS`:

```makefile
COMPRESSION_LIBS = -L$(INTERNAL_GRIB2_PATH)/lib -ljasper -lpng -lz
```

Acrescente `$(INTERNAL_GRIB2_PATH)/lib64`, mantendo também o diretório `lib`:

```makefile
COMPRESSION_LIBS = -L$(INTERNAL_GRIB2_PATH)/lib -L$(INTERNAL_GRIB2_PATH)/lib64 -ljasper -lpng -lz
```

`INTERNAL_GRIB2_PATH` é definido pelo processo de compilação como o diretório `grib2` da instalação atual do WPS. Dessa forma, a configuração não depende do nome do usuário nem do caminho absoluto do repositório.

Confira também o caminho dos cabeçalhos, que não precisa de alteração:

```makefile
COMPRESSION_INC = -I$(INTERNAL_GRIB2_PATH)/include
```

## 6. Compilar somente o `ungrib`

Execute a compilação e grave toda a saída fora do diretório do código-fonte:

```bash
cd ~/git/WPS
./compile ungrib > ~/compile_ungrib.log 2>&1
```

Para acompanhar o andamento em outro terminal:

```bash
tail -f ~/compile_ungrib.log
```

Essa etapa compila as bibliotecas de suporte a GRIB2, as bibliotecas NCEP `w3` e `g2` e, por fim, o `ungrib.exe`.

## 7. Validar o resultado

Não considere apenas o código de retorno do script de compilação. O processo de build do WPS utiliza `make -i` em algumas etapas e pode ignorar erros. Verifique explicitamente o executável:

```bash
cd ~/git/WPS

test -x ungrib.exe && echo "ungrib compilado com sucesso"
ls -lhL ungrib.exe
ls -lh ungrib/src/ungrib.exe
file ungrib.exe
```

O arquivo deve existir, ter tamanho maior que zero e ser identificado como um executável ELF.

O diretório principal normalmente contém um link simbólico:

```text
ungrib.exe -> ungrib/src/ungrib.exe
```

## 8. Avisos observados durante a compilação

### Autotools ausentes

O log pode conter mensagens como:

```text
aclocal-1.14: command not found
automake-1.14: command not found
autoconf: command not found
```

Na compilação validada, essas mensagens apareceram acompanhadas de `(ignored)` e não impediram a criação das bibliotecas nem do `ungrib.exe`.

### Avisos do compilador Cray

O CCE pode emitir diversos avisos sobre uma variável interna chamada `la`. Eles não impediram a compilação quando o resumo indicou zero erros:

```text
Cray Fortran : 0 errors
```

### Aviso sobre `tmpnam`

A linkedição da biblioteca JasPer pode mostrar:

```text
warning: the use of `tmpnam' is dangerous, better use `mkstemp'
```

Esse aviso não impediu a criação do executável.

## 9. Solução de problemas

### `cannot find -ljasper`

Confirme que a biblioteca foi instalada:

```bash
ls -lh grib2/lib64/libjasper.a
ls -lh grib2/lib64/libpng.a
```

Depois confira se `COMPRESSION_LIBS` contém `-L$(INTERNAL_GRIB2_PATH)/lib64`. Após corrigir o arquivo, não é necessário limpar ou reconfigurar; execute novamente:

```bash
./compile ungrib > ~/compile_ungrib.log 2>&1
```

### Compilação interrompida

Se o final do log contiver mensagens como:

```text
Interrupt (ignored)
```

a compilação recebeu uma interrupção externa, normalmente `Ctrl+C` ou o encerramento da sessão. Retome sem executar `./clean -a`:

```bash
./compile ungrib > ~/compile_ungrib.log 2>&1
```

### `ungrib.exe` ausente apesar do término do script

Procure no final do log por erros reais de linkedição:

```bash
tail -n 100 ~/compile_ungrib.log
```

Os indicadores mais importantes são:

```text
cannot find
undefined reference
Interrupt
```

## 10. Executar o `ungrib`

Carregue o mesmo ambiente usado na compilação:

```bash
module load PrgEnv-cray/8.6.0
cd ~/git/WPS
```

O fluxo básico de execução é:

1. configurar as seções `&share` e `&ungrib` de `namelist.wps`;
2. criar um link chamado `Vtable` para a tabela compatível com os dados meteorológicos;
3. criar os links `GRIBFILE.*` com `link_grib.csh`;
4. executar `./ungrib.exe`;
5. conferir `ungrib.log` e os arquivos intermediários produzidos.

O `ungrib.exe` deve ser executado com um único processo, sem `mpiexec` ou `mpirun`.

## Referências

- [Repositório oficial do WPS](https://github.com/wrf-model/WPS)
- [Guia oficial de compilação do WRF e WPS](https://www2.mmm.ucar.edu/wrf/site/documentation/users_guide/compiling.html)
- [Documentação oficial do WPS](https://www2.mmm.ucar.edu/wrf/site/documentation/users_guide/wps.html)
