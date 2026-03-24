#!/usr/bin/env python3
"""
Baixa dados do ERA5 e executa o fluxo do WPS ate o ungrib.

Escopo:
- download de arquivos GRIB do ERA5 em niveis de pressao e superficie
- geracao de um namelist.wps minimo para o ungrib
- preparacao do diretorio de trabalho do WPS
- execucao do link_grib.csh
- execucao do ungrib.exe

O script nao executa o init_atmosphere.
"""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path
import shutil
import subprocess
import sys


DEFAULT_GRID = "0.25/0.25"
DEFAULT_PREFIX = "ERA5"
DEFAULT_INTERVAL_HOURS = 3
DEFAULT_PRESSURE_LEVELS = [
    "10",
    "30",
    "50",
    "70",
    "100",
    "150",
    "200",
    "250",
    "300",
    "350",
    "400",
    "500",
    "600",
    "650",
    "700",
    "750",
    "775",
    "800",
    "825",
    "850",
    "875",
    "900",
    "925",
    "950",
    "975",
    "1000",
]
PRESSURE_VARIABLES = [
    "geopotential",
    "relative_humidity",
    "temperature",
    "u_component_of_wind",
    "v_component_of_wind",
]
SURFACE_VARIABLES = [
    "10m_u_component_of_wind",
    "10m_v_component_of_wind",
    "2m_dewpoint_temperature",
    "2m_temperature",
    "geopotential",
    "land_sea_mask",
    "mean_sea_level_pressure",
    "sea_ice_cover",
    "sea_surface_temperature",
    "skin_temperature",
    "snow_depth",
    "soil_temperature_level_1",
    "soil_temperature_level_2",
    "soil_temperature_level_3",
    "soil_temperature_level_4",
    "surface_pressure",
    "volumetric_soil_water_layer_1",
    "volumetric_soil_water_layer_2",
    "volumetric_soil_water_layer_3",
    "volumetric_soil_water_layer_4",
]
DATETIME_FORMATS = (
    "%Y-%m-%d_%H",
    "%Y-%m-%d_%H:%M",
    "%Y-%m-%d_%H:%M:%S",
    "%Y-%m-%dT%H",
    "%Y-%m-%dT%H:%M",
    "%Y-%m-%dT%H:%M:%S",
)


def parse_datetime(value: str) -> dt.datetime:
    for fmt in DATETIME_FORMATS:
        try:
            return dt.datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise argparse.ArgumentTypeError(
        "Use uma data no formato YYYY-MM-DD_HH, YYYY-MM-DD_HH:MM "
        "ou YYYY-MM-DD_HH:MM:SS."
    )


def parse_pressure_levels(value: str) -> list[str]:
    levels = [item.strip() for item in value.split(",") if item.strip()]
    if not levels:
        raise argparse.ArgumentTypeError(
            "Informe ao menos um nivel de pressao em --pressure-levels."
        )
    return levels


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Executa o fluxo ERA5 -> link_grib -> ungrib em um diretorio "
            "de trabalho dedicado."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--start",
        required=True,
        type=parse_datetime,
        help="Data inicial da serie temporal.",
    )
    parser.add_argument(
        "--end",
        required=True,
        type=parse_datetime,
        help="Data final da serie temporal. O horario final e inclusivo.",
    )
    parser.add_argument(
        "--interval-hours",
        type=int,
        default=DEFAULT_INTERVAL_HOURS,
        help="Passo temporal, em horas, entre os downloads.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Diretorio raiz da execucao.",
    )
    parser.add_argument(
        "--download-dir",
        type=Path,
        help="Diretorio onde os GRIBs serao armazenados.",
    )
    parser.add_argument(
        "--wps-workdir",
        type=Path,
        help="Diretorio de trabalho do WPS para link_grib e ungrib.",
    )
    parser.add_argument(
        "--wps-dir",
        required=True,
        type=Path,
        help="Diretorio raiz de uma instalacao do WPS.",
    )
    parser.add_argument(
        "--link-grib",
        type=Path,
        help="Caminho explicito para o link_grib.csh.",
    )
    parser.add_argument(
        "--ungrib-exe",
        type=Path,
        help="Caminho explicito para o ungrib.exe.",
    )
    parser.add_argument(
        "--vtable",
        type=Path,
        help="Caminho explicito para a Vtable a ser usada.",
    )
    parser.add_argument(
        "--prefix",
        default=DEFAULT_PREFIX,
        help="Prefixo dos arquivos intermediarios gerados pelo ungrib.",
    )
    parser.add_argument(
        "--grid",
        default=DEFAULT_GRID,
        help="Resolucao da grade pedida ao CDS, no formato lat/lon.",
    )
    parser.add_argument(
        "--pressure-levels",
        type=parse_pressure_levels,
        default=DEFAULT_PRESSURE_LEVELS,
        help="Lista de niveis de pressao separados por virgula.",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Nao baixa novamente os GRIBs e reutiliza arquivos existentes.",
    )
    parser.add_argument(
        "--overwrite-downloads",
        action="store_true",
        help="Sobrescreve os GRIBs existentes durante o download.",
    )
    return parser


def ensure_valid_dates(start: dt.datetime, end: dt.datetime, interval_hours: int) -> None:
    if interval_hours <= 0:
        raise ValueError("--interval-hours deve ser maior que zero.")
    if end < start:
        raise ValueError("--end deve ser maior ou igual a --start.")

    total_seconds = int((end - start).total_seconds())
    interval_seconds = interval_hours * 3600
    if total_seconds % interval_seconds != 0:
        raise ValueError(
            "A diferenca entre --start e --end deve ser multipla de --interval-hours."
        )


def iter_times(
    start: dt.datetime,
    end: dt.datetime,
    interval_hours: int,
) -> list[dt.datetime]:
    times = []
    current = start
    delta = dt.timedelta(hours=interval_hours)
    while current <= end:
        times.append(current)
        current += delta
    return times


def grib_paths(download_dir: Path, when: dt.datetime) -> tuple[Path, Path]:
    timestamp = when.strftime("%Y%m%d_%H%M")
    pressure_file = download_dir / f"era5_pl_{timestamp}.grib"
    surface_file = download_dir / f"era5_sfc_{timestamp}.grib"
    return pressure_file, surface_file


def print_step(message: str) -> None:
    print(f"[ERA5/WPS] {message}")


def snapshot_existing_paths(root_dir: Path) -> set[Path]:
    if not root_dir.exists():
        return set()

    snapshot = {Path(".")}
    for path in root_dir.rglob("*"):
        snapshot.add(path.relative_to(root_dir))
    return snapshot


def ensure_wps_paths(args: argparse.Namespace) -> tuple[Path, Path, Path]:
    wps_dir = args.wps_dir.expanduser().resolve()
    link_grib = (
        args.link_grib.expanduser().resolve()
        if args.link_grib
        else (wps_dir / "link_grib.csh").resolve()
    )
    ungrib_exe = (
        args.ungrib_exe.expanduser().resolve()
        if args.ungrib_exe
        else (wps_dir / "ungrib.exe").resolve()
    )
    vtable = (
        args.vtable.expanduser().resolve()
        if args.vtable
        else (wps_dir / "ungrib" / "Variable_Tables" / "Vtable.ECMWF").resolve()
    )

    missing_paths = [
        path for path in (wps_dir, link_grib, ungrib_exe, vtable) if not path.exists()
    ]
    if missing_paths:
        formatted = "\n".join(f"- {path}" for path in missing_paths)
        raise FileNotFoundError(f"Arquivos/diretorios do WPS nao encontrados:\n{formatted}")

    return link_grib, ungrib_exe, vtable


def ensure_cds_client():
    try:
        import cdsapi
    except ImportError as exc:
        raise RuntimeError(
            "O pacote cdsapi nao esta instalado. Instale-o antes de rodar o script."
        ) from exc

    return cdsapi.Client()


def retrieve_dataset(
    client,
    dataset: str,
    payload: dict[str, object],
    target: Path,
    overwrite: bool,
) -> None:
    if target.exists() and not overwrite:
        print_step(f"Reutilizando arquivo existente: {target}")
        return

    target.parent.mkdir(parents=True, exist_ok=True)
    print_step(f"Baixando {dataset} -> {target}")
    client.retrieve(dataset, payload, str(target))


def build_request_base(
    when: dt.datetime,
    grid: str,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "product_type": "reanalysis",
        "format": "grib",
        "grid": grid,
        "year": f"{when.year:04d}",
        "month": f"{when.month:02d}",
        "day": f"{when.day:02d}",
        "time": f"{when.hour:02d}:{when.minute:02d}",
    }
    return payload


def download_era5_files(
    times: list[dt.datetime],
    download_dir: Path,
    grid: str,
    pressure_levels: list[str],
    overwrite: bool,
) -> list[Path]:
    client = ensure_cds_client()
    ordered_files: list[Path] = []

    for when in times:
        pressure_file, surface_file = grib_paths(download_dir, when)
        ordered_files.extend([pressure_file, surface_file])

        base_request = build_request_base(when, grid)
        pressure_request = dict(base_request)
        pressure_request["variable"] = PRESSURE_VARIABLES
        pressure_request["pressure_level"] = pressure_levels

        surface_request = dict(base_request)
        surface_request["variable"] = SURFACE_VARIABLES

        retrieve_dataset(
            client=client,
            dataset="reanalysis-era5-pressure-levels",
            payload=pressure_request,
            target=pressure_file,
            overwrite=overwrite,
        )
        retrieve_dataset(
            client=client,
            dataset="reanalysis-era5-single-levels",
            payload=surface_request,
            target=surface_file,
            overwrite=overwrite,
        )

    return ordered_files


def ensure_existing_gribs(times: list[dt.datetime], download_dir: Path) -> list[Path]:
    ordered_files: list[Path] = []
    missing_files: list[Path] = []

    for when in times:
        pressure_file, surface_file = grib_paths(download_dir, when)
        ordered_files.extend([pressure_file, surface_file])
        for path in (pressure_file, surface_file):
            if not path.exists():
                missing_files.append(path)

    if missing_files:
        formatted = "\n".join(f"- {path}" for path in missing_files)
        raise FileNotFoundError(
            "Foram solicitados arquivos locais, mas alguns GRIBs nao existem:\n"
            f"{formatted}"
        )

    return ordered_files


def render_namelist_wps(
    start: dt.datetime,
    end: dt.datetime,
    interval_hours: int,
    prefix: str,
) -> str:
    start_wps = start.strftime("%Y-%m-%d_%H:%M:%S")
    end_wps = end.strftime("%Y-%m-%d_%H:%M:%S")
    interval_seconds = interval_hours * 3600

    return f"""&share
 wrf_core = 'ARW',
 max_dom = 1,
 start_date = '{start_wps}',
 end_date   = '{end_wps}',
 interval_seconds = {interval_seconds},
 io_form_geogrid = 2,
/

&geogrid
 parent_id         = 1,
 parent_grid_ratio = 1,
 i_parent_start    = 1,
 j_parent_start    = 1,
 e_we              = 10,
 e_sn              = 10,
 dx = 1.0,
 dy = 1.0,
 map_proj = 'lat-lon',
 ref_lat   = 0.0,
 ref_lon   = 0.0,
 truelat1  = 0.0,
 truelat2  = 0.0,
 stand_lon = 0.0,
 geog_data_path = '/tmp',
 geog_data_res  = 'default',
 opt_output_from_geogrid_path = './',
/

&ungrib
 out_format = 'WPS',
 prefix = '{prefix}',
/

&metgrid
 fg_name = '{prefix}',
 io_form_metgrid = 2,
/
"""


def replace_file_with_symlink_or_copy(source: Path, target: Path) -> None:
    if target.exists() or target.is_symlink():
        target.unlink()

    try:
        target.symlink_to(source)
    except OSError:
        shutil.copy2(source, target)


def cleanup_grib_links(workdir: Path) -> None:
    for path in workdir.glob("GRIBFILE.*"):
        if path.is_file() or path.is_symlink():
            path.unlink()


def prepare_wps_workdir(
    workdir: Path,
    vtable_source: Path,
    namelist_content: str,
) -> None:
    workdir.mkdir(parents=True, exist_ok=True)
    cleanup_grib_links(workdir)
    (workdir / "namelist.wps").write_text(namelist_content, encoding="utf-8")
    replace_file_with_symlink_or_copy(vtable_source, workdir / "Vtable")


def build_link_grib_command(link_grib: Path, grib_files: list[Path]) -> list[str]:
    command = [str(link_grib)]
    if (link_grib.stat().st_mode & 0o111) == 0:
        csh = shutil.which("csh")
        if csh is None:
            raise RuntimeError(
                "link_grib.csh nao esta executavel e o interpretador csh nao foi encontrado."
            )
        command = [csh, str(link_grib)]

    command.extend(str(path) for path in grib_files)
    return command


def run_command(command: list[str], workdir: Path) -> None:
    command_as_text = " ".join(command)
    print_step(f"Executando em {workdir}: {command_as_text}")
    subprocess.run(command, cwd=workdir, check=True)


def run_wps_ungrib(
    workdir: Path,
    link_grib: Path,
    ungrib_exe: Path,
    grib_files: list[Path],
) -> None:
    link_grib_command = build_link_grib_command(link_grib, grib_files)
    run_command(link_grib_command, workdir)
    run_command([str(ungrib_exe)], workdir)


def collect_intermediate_files(workdir: Path, prefix: str) -> list[Path]:
    return sorted(workdir.glob(f"{prefix}:*"))


def ensure_no_output_conflicts(
    output_dir: Path,
    existing_relpaths: set[Path],
    final_files: list[Path],
) -> None:
    for final_file in final_files:
        target = output_dir / final_file.name
        if not target.exists():
            continue

        relpath = target.relative_to(output_dir)
        if relpath in existing_relpaths:
            raise FileExistsError(
                "Ja existe em output-dir um arquivo com o nome final "
                f"{target.name}. Escolha outro output-dir ou remova o arquivo existente."
            )


def move_final_files_to_output_dir(
    output_dir: Path,
    final_files: list[Path],
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    moved_files: list[Path] = []

    for final_file in final_files:
        target = output_dir / final_file.name

        if target.exists():
            if target.is_file() or target.is_symlink():
                target.unlink()
            else:
                raise IsADirectoryError(
                    f"O destino final {target} existe e nao e um arquivo regular."
                )

        shutil.move(str(final_file), str(target))
        moved_files.append(target)

    return moved_files


def add_path_and_parents_to_keep(
    keep_relpaths: set[Path],
    output_dir: Path,
    path: Path,
) -> None:
    try:
        relpath = path.relative_to(output_dir)
    except ValueError:
        return

    keep_relpaths.add(relpath)
    for parent in relpath.parents:
        keep_relpaths.add(parent)


def cleanup_output_dir(
    output_dir: Path,
    existing_relpaths: set[Path],
    paths_to_keep: list[Path],
) -> None:
    if not output_dir.exists():
        return

    keep_relpaths = set(existing_relpaths)
    keep_relpaths.add(Path("."))

    for kept_path in paths_to_keep:
        add_path_and_parents_to_keep(keep_relpaths, output_dir, kept_path)

    all_paths = sorted(
        output_dir.rglob("*"),
        key=lambda path: len(path.relative_to(output_dir).parts),
        reverse=True,
    )

    for path in all_paths:
        relpath = path.relative_to(output_dir)
        if relpath in keep_relpaths:
            continue

        if path.is_symlink() or path.is_file():
            path.unlink()
        elif path.is_dir():
            try:
                path.rmdir()
            except OSError:
                pass


def remove_intermediate_dirs(output_dir: Path, *directories: Path) -> None:
    for directory in directories:
        try:
            directory.relative_to(output_dir)
        except ValueError:
            continue

        if directory == output_dir or not directory.exists():
            continue

        shutil.rmtree(directory)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    ensure_valid_dates(args.start, args.end, args.interval_hours)

    output_dir = args.output_dir.expanduser().resolve()
    existing_output_paths = snapshot_existing_paths(output_dir)
    download_dir = (
        args.download_dir.expanduser().resolve()
        if args.download_dir
        else output_dir / "downloads"
    )
    wps_workdir = (
        args.wps_workdir.expanduser().resolve()
        if args.wps_workdir
        else output_dir / "wps_work"
    )
    link_grib, ungrib_exe, vtable = ensure_wps_paths(args)
    times = iter_times(args.start, args.end, args.interval_hours)

    print_step(f"Total de horarios solicitados: {len(times)}")
    print_step(f"Diretorio de download: {download_dir}")
    print_step(f"Diretorio de trabalho do WPS: {wps_workdir}")

    if args.skip_download:
        print_step("Pulando o download e reutilizando os GRIBs existentes.")
        grib_files = ensure_existing_gribs(times, download_dir)
    else:
        grib_files = download_era5_files(
            times=times,
            download_dir=download_dir,
            grid=args.grid,
            pressure_levels=args.pressure_levels,
            overwrite=args.overwrite_downloads,
        )

    namelist_content = render_namelist_wps(
        start=args.start,
        end=args.end,
        interval_hours=args.interval_hours,
        prefix=args.prefix,
    )
    prepare_wps_workdir(
        workdir=wps_workdir,
        vtable_source=vtable,
        namelist_content=namelist_content,
    )
    run_wps_ungrib(
        workdir=wps_workdir,
        link_grib=link_grib,
        ungrib_exe=ungrib_exe,
        grib_files=grib_files,
    )

    intermediate_files = collect_intermediate_files(wps_workdir, args.prefix)
    ensure_no_output_conflicts(
        output_dir=output_dir,
        existing_relpaths=existing_output_paths,
        final_files=intermediate_files,
    )
    final_files = move_final_files_to_output_dir(
        output_dir=output_dir,
        final_files=intermediate_files,
    )
    cleanup_output_dir(
        output_dir=output_dir,
        existing_relpaths=existing_output_paths,
        paths_to_keep=final_files,
    )
    remove_intermediate_dirs(output_dir, download_dir, wps_workdir)
    print_step(
        "Fluxo concluido. "
        f"Arquivos finais do ungrib encontrados: {len(final_files)}"
    )
    print_step(f"Consulte os resultados em: {output_dir}")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        print(
            f"[ERA5/WPS] Erro ao executar um comando externo: {exc}",
            file=sys.stderr,
        )
        raise SystemExit(exc.returncode or 1)
    except Exception as exc:  # pragma: no cover - caminho de erro operacional
        print(f"[ERA5/WPS] {exc}", file=sys.stderr)
        raise SystemExit(1)
