"""Implement queries for polars dataframes to be used in shape-matching.

Specifically, these queries support the following pipeline:
    - Compute pre-alignment of mesh
    - Compute (W)ECT on the pre-aligned mesh
    - Compute an embedding/post-processing of the (W)ECT.

This whole pipeline can be called using compute_db_entry().
"""

import polars as pl

from ..utils import unflatten_to_matrix
from ..params import ComplexInfo, MapArgs, EctArgs, WeightedComplexInfo, MapCopyArgs
from .register import (
    pre_align_copy_wect,
    wect,
    pre_align_wect,
    # pre_align_copy_ect,
    # pre_align_ect,
    ect,
)

""" WECTS """


def premapped_copy_wects(
    wci: WeightedComplexInfo,
    ma: MapCopyArgs,
    ea: EctArgs,
) -> pl.Expr:
    """Compute the WECTs for the given simplices and weights.

    The simplices and weights columns are each flattened structs.
    Before computing the WECTs, the mesh is mapped with a rigid transformation
    to ensure the WECT is invariant to a rigid transformation of the input.
    In some cases, this results in multiple WECTs being returned by this call,
    corresponding to different transformations of the input mesh.

    Args:
        wci: Information about the simplices and weights of the mesh.
        ma: Arguments for the mapping of the mesh.
        ea: Arguments for the WECTs.

    Returns:
        A column of WECTs. Each WECT is a flattened matrix.
    """
    wects = pre_align_copy_wect(
        pl.col(wci.simplices),
        pl.col(wci.weights),
        provided_simplices=wci.provided_simplices,
        provided_weights=wci.provided_weights,
        embedded_dimension=wci.vdim,
        num_heights=ea.steps,
        num_directions=ea.directions,
        align_dimension=ma.align_dimension,
        subsample_ratio=ma.subsample_ratio,
        subsample_min=ma.subsample_min,
        subsample_max=ma.subsample_max,
        eps=ma.eps,
        copies=ma.copies,
    )  # output column of (n * d * d) flattened array of flattened matrices

    # Reshape the maps
    wects = unflatten_to_matrix(
        wects, ea.steps * ea.directions
    )  # now (n)-list of num_height * num_direction flattened matrices

    return wects


def premapped_wects(
    wci: WeightedComplexInfo,
    ma: MapArgs,
    ea: EctArgs,
) -> pl.Expr:
    """Compute the WECT for the given simplices and weights.

    Before computing the WECTs, the mesh is mapped to point the weighted centroid
    vector in the positive ndrant.

    Args:
        wci: Information about the simplices and weights of the mesh.
        ma: Arguments for the mapping of the mesh.
        wa: Arguments for the WECTs.

    Returns:
        A column of WECTs. Each WECT is a flattened matrix.
    """
    wects = pre_align_wect(
        pl.col(wci.simplices),
        pl.col(wci.weights),
        provided_simplices=wci.provided_simplices,
        provided_weights=wci.provided_weights,
        embedded_dimension=wci.vdim,
        num_heights=ea.steps,
        num_directions=ea.directions,
        align_dimension=ma.align_dimension,
        subsample_ratio=ma.subsample_ratio,
        subsample_min=ma.subsample_min,
        subsample_max=ma.subsample_max,
    )

    return wects  # flattened wect


# def _get_embedding_expr(
#     veccol: pl.Expr,
#     embedder: Embedder,
# ) -> pl.Expr:
#     # obtain call to gufunc so polars recognizes signature
#     emb_gufunc = embedder.get_gufunc()
#     args = embedder.get_gufunc_args()
#     return veccol.map_batches(
#         lambda t: emb_gufunc(t, *args),
#         return_dtype=pl.array(pl.float64, embedder.emb_dim),
#         is_elementwise=true,
#     )


def with_premapped_copy_wects(
    df: pl.LazyFrame | pl.DataFrame,
    wci: WeightedComplexInfo,
    ma: MapCopyArgs,
    ea: EctArgs,
    wname: str,
) -> pl.LazyFrame:
    """Compute all premapped WECTs for the given mesh data and transofrmations.

    Args:
        df: The dataframe containing the mesh data.
        wci: Information about the simplices and weights of the mesh.
        ma: Arguments for the mapping of the mesh.
        ea: Arguments for the WECTs.
        wname: The name of the column to store the computed WECTs.

    Returns:
        A lazyframe with the computed WECTs. The rows correspond to each WECT
        given by a transformation on an object.
    """
    return df.lazy().with_columns(premapped_copy_wects(wci, ma, ea).alias(wname))


def with_premapped_wects(
    df: pl.LazyFrame | pl.DataFrame,
    wci: WeightedComplexInfo,
    ma: MapArgs,
    ea: EctArgs,
    wname: str,
) -> pl.LazyFrame:
    """Compute the WECT for each given simplicial complex, premapping the mesh before computing the WECT.

    Args:
        df: The dataframe containing the mesh data.
        wci: Information about the simplices and weights of the mesh.
        ma: Arguments for the mapping of the mesh.
        ea: Arguments for the WECTs.
        wname: The name of the column to store the computed WECTs.

    Returns:
        A lazyframe with the computed WECTs. The rows correspond to each WECT
        given by a transformation on an object.

    """
    return df.lazy().with_columns(premapped_wects(wci, ma, ea).alias(wname))


def wects(
    wci: WeightedComplexInfo,
    ea: EctArgs,
) -> pl.Expr:
    """Compute the WECTs for the given simplices and weights. The simplices and weights columns are each flattened structs.

    Args:
        wci: Information about the simplices and weights of the mesh.
        ea: Arguments for the WECTs.
    """
    wects = wect(
        pl.col(wci.simplices),
        pl.col(wci.weights),
        provided_simplices=wci.provided_simplices,
        provided_weights=wci.provided_weights,
        embedded_dimension=wci.vdim,
        num_heights=ea.steps,
        num_directions=ea.directions,
    )  # output column of (n * d * d) flattened array of flattened matrices

    # Reshape the maps
    wects = unflatten_to_matrix(
        wects, ea.steps * ea.directions
    )  # now (n)-list of num_height * num_direction flattened matrices

    return wects


# def _get_embedding_expr(
#     veccol: pl.Expr,
#     embedder: Embedder,
# ) -> pl.Expr:
#     # obtain call to gufunc so polars recognizes signature
#     emb_gufunc = embedder.get_gufunc()
#     args = embedder.get_gufunc_args()
#     return veccol.map_batches(
#         lambda t: emb_gufunc(t, *args),
#         return_dtype=pl.array(pl.float64, embedder.emb_dim),
#         is_elementwise=true,
#     )


def with_wects(
    df: pl.LazyFrame | pl.DataFrame,
    wci: WeightedComplexInfo,
    ea: EctArgs,
    wname: str,
) -> pl.LazyFrame:
    """Compute the WECTs for the given mesh data and transofrmations.

    Returns:
        A lazyframe with the computed WECTs. The rows correspond to each WECT
        given by a transformation on an object.

    """
    return df.lazy().with_columns(wects(wci, ea).alias(wname))


""" ECTS """


def ects(
    ci: ComplexInfo,
    ea: EctArgs,
) -> pl.Expr:
    """Compute the ECTs for the given simplices. The simplices and weights columns are each flattened structs.

    Args:
        ci: Information about the simplices and weights of the mesh.
        ea: Arguments for the ECTs.
    """
    ects = ect(
        pl.col(ci.simplices),
        provided_simplices=ci.provided_simplices,
        embedded_dimension=ci.vdim,
        num_heights=ea.steps,
        num_directions=ea.directions,
    )  # output column of (n * d * d) flattened array of flattened matrices

    # Reshape the maps
    ects = unflatten_to_matrix(
        ects, ea.steps * ea.directions
    )  # now (n)-list of num_height * num_direction flattened matrices

    return ects


def with_ects(
    df: pl.LazyFrame | pl.DataFrame,
    ci: ComplexInfo,
    ea: EctArgs,
    ename: str,
) -> pl.LazyFrame:
    """Compute the ECT for the given mesh data and transofrmations.

    Returns:
        A lazyframe with the computed ECTs. The rows correspond to each ECT
        given by a transformation on an object.

    """
    return df.lazy().with_columns(ects(ci, ea).alias(ename))


# def premapped_copy_ects(
#     ci: ComplexInfo,
#     ma: MapCopyArgs,
#     ea: EctArgs,
# ) -> pl.Expr:
#     """Compute the ECTs for the given simplices.
#
#     The simplices and weights columns are each flattened structs.
#     Before computing the ECTs, the mesh is mapped with a rigid transformation
#     to ensure the ECT is invariant to a rigid transformation of the input.
#     In some cases, this results in multiple ECTs being returned by this call,
#     corresponding to different transformations of the input mesh.
#
#     Args:
#         ci: Information about the simplices and weights of the mesh.
#         ma: Arguments for the mapping of the mesh.
#         ea: Arguments for the ECTs.
#
#     Returns:
#         A column of ECTs. Each ECT is a flattened matrix.
#     """
#     ects = pre_align_copy_ect(
#         pl.col(ci.simplices),
#         provided_simplices=ci.provided_simplices,
#         embedded_dimension=ci.vdim,
#         num_steps=ea.steps,
#         num_directions=ea.directions,
#         align_dimension=ma.align_dimension,
#         subsample_ratio=ma.subsample_ratio,
#         subsample_min=ma.subsample_min,
#         subsample_max=ma.subsample_max,
#         eps=ma.eps,
#         copies=ma.copies,
#     )  # output column of (n * d * d) flattened array of flattened matrices
#
#     # Reshape the maps
#     ects = unflatten_to_matrix(
#         ects, ea.steps * ea.directions
#     )  # now (n)-list of num_height * num_direction flattened matrices
#
#     return ects
#
#
# def premapped_ects(
#     ci: ComplexInfo,
#     ma: MapArgs,
#     ea: EctArgs,
# ) -> pl.Expr:
#     """Compute the ECT for the given simplices.
#
#     Before computing the ECTs, the mesh is mapped to point the weighted centroid
#     vector in the positive ndrant.
#
#     Args:
#         ci: Information about the simplices and weights of the mesh.
#         ma: Arguments for the mapping of the mesh.
#         ea: Arguments for the ECTs.
#
#     Returns:
#         A column of ECTs. Each ECT is a flattened matrix.
#     """
#     ects = pre_align_ect(
#         pl.col(ci.simplices),
#         provided_simplices=ci.provided_simplices,
#         embedded_dimension=ci.vdim,
#         num_directions=ea.directions,
#         num_steps=ea.steps,
#         align_dimension=ma.align_dimension,
#         subsample_ratio=ma.subsample_ratio,
#         subsample_min=ma.subsample_min,
#         subsample_max=ma.subsample_max,
#     )
#
#     return ects  # flattened wect

# def with_premapped_copy_ects(
#     df: pl.LazyFrame | pl.DataFrame,
#     ci: ComplexInfo,
#     ma: MapCopyArgs,
#     ea: EctArgs,
#     ename: str,
# ) -> pl.LazyFrame:
#     """Compute all premapped ECTs for the given mesh data and transofrmations.
#
#     Args:
#         df: The dataframe containing the mesh data.
#         ci: Information about the simplices and weights of the mesh.
#         ma: Arguments for the mapping of the mesh.
#         ea: Arguments for the ECTs.
#         ename: The name of the column to store the computed ECTs.
#
#     Returns:
#         A lazyframe with the computed ECTs. The rows correspond to each ECT
#         given by a transformation on an object.
#     """
#     return df.lazy().with_columns(premapped_copy_ects(ci, ma, ea).alias(ename))
#
#
# def with_premapped_ects(
#     df: pl.LazyFrame | pl.DataFrame,
#     ci: ComplexInfo,
#     ma: MapArgs,
#     ea: EctArgs,
#     ename: str,
# ) -> pl.LazyFrame:
#     """Compute the ECT for each given simplicial complex, premapping the mesh before computing the ECT.
#
#     Args:
#         df: The dataframe containing the mesh data.
#         ci: Information about the simplices and weights of the mesh.
#         ma: Arguments for the mapping of the mesh.
#         ea: Arguments for the ECTs.
#         ename: The name of the column to store the computed ECTs.
#
#     Returns:
#         A lazyframe with the computed ECTs. The rows correspond to each ECT
#         given by a transformation on an object.
#
#     """
#     return df.lazy().with_columns(premapped_ects(ci, ma, ea).alias(ename))
