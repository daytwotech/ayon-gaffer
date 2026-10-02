# GafferComp integration

This fork keeps the AYON host name as `gaffer` and treats GafferComp as a
Gaffer extension/application rather than a separate DCC host.

## AYON application variant

Create a Gaffer application variant named **GafferComp** using the same Gaffer
executable/version as the GafferComp build.

Set:

- `GAFFERCOMP_ROOT` to the root of the packaged GafferComp build.
- launch arguments so the Gaffer executable starts the `comp` application.

The addon prepends `GAFFERCOMP_ROOT` to `GAFFER_EXTENSION_PATHS` and then
adds AYON's deploy and GafferDeadline extension paths. Python's `os.pathsep`
is used, so this works on Windows and Linux.

Do not launch `gaffercomp.cmd`/the shell wrapper from AYON; AYON should own
the environment and launch Gaffer directly.

## Behaviour

When GafferComp is available:

- AYON image loads still create stock `GafferImage.ImageReader` nodes, then
  apply GafferComp's Nuke-style sequence hold behaviour.
- Render2D creation creates `GafferComp.Write` directly and imprints the
  normal AYON creator metadata on it.
- Local rendering calls `Write.render()`.
- Frame collection uses `Write.frames()`.
- Deadline dispatch treats the Write as a normal Gaffer task node.

When GafferComp is not available the existing `AyonGaffer::Render2D` box
workflow remains unchanged.

## Farm requirement

The Deadline worker must receive the same `GAFFERCOMP_ROOT` /
`GAFFER_EXTENSION_PATHS` setup before Gaffer deserializes the workfile.
Otherwise `GafferComp::Write` will not be registered and the script cannot
load correctly.

Package GafferComp separately for each supported OS and Gaffer build/ABI.
