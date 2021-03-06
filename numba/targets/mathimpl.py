"""
Provide math calls that uses intrinsics or libc math functions.
"""

from __future__ import print_function, absolute_import, division
import math
import llvm.core as lc
from llvm.core import Type
from numba.targets.imputils import implement, impl_attribute, builtin_attr
from numba import types, cgutils, utils
from numba.typing import signature


functions = []


def register(f):
    functions.append(f)
    return f


def unary_math_int_impl(fn, f64impl):
    @register
    @implement(fn, types.int64)
    def s64impl(context, builder, sig, args):
        [val] = args
        fpval = builder.sitofp(val, Type.double())
        sig = signature(types.float64, types.float64)
        return f64impl(context, builder, sig, [fpval])

    @register
    @implement(fn, types.uint64)
    def u64impl(context, builder, sig, args):
        [val] = args
        fpval = builder.uitofp(val, Type.double())
        sig = signature(types.float64, types.float64)
        return f64impl(context, builder, sig, [fpval])


def unary_math_intr(fn, intrcode):
    @register
    @implement(fn, types.float32)
    def f32impl(context, builder, sig, args):
        [val] = args
        mod = cgutils.get_module(builder)
        lty = context.get_value_type(types.float32)
        intr = lc.Function.intrinsic(mod, intrcode, [lty])
        return builder.call(intr, args)

    @register
    @implement(fn, types.float64)
    def f64impl(context, builder, sig, args):
        [val] = args
        mod = cgutils.get_module(builder)
        lty = context.get_value_type(types.float64)
        intr = lc.Function.intrinsic(mod, intrcode, [lty])
        return builder.call(intr, args)

    unary_math_int_impl(fn, f64impl)


def unary_math_extern(fn, f32extern, f64extern):
    @register
    @implement(fn, types.float32)
    def f32impl(context, builder, sig, args):
        [val] = args
        mod = cgutils.get_module(builder)
        fnty = Type.function(Type.float(), [Type.float()])
        fn = mod.get_or_insert_function(fnty, name=f32extern)
        return builder.call(fn, (val,))

    @register
    @implement(fn, types.float64)
    def f64impl(context, builder, sig, args):
        [val] = args
        mod = cgutils.get_module(builder)
        fnty = Type.function(Type.double(), [Type.double()])
        fn = mod.get_or_insert_function(fnty, name=f64extern)
        return builder.call(fn, (val,))

    unary_math_int_impl(fn, f64impl)


unary_math_intr(math.fabs, lc.INTR_FABS)
#unary_math_intr(math.sqrt, lc.INTR_SQRT)
unary_math_intr(math.exp, lc.INTR_EXP)
unary_math_intr(math.log, lc.INTR_LOG)
unary_math_intr(math.log10, lc.INTR_LOG10)
unary_math_intr(math.sin, lc.INTR_SIN)
unary_math_intr(math.cos, lc.INTR_COS)
#unary_math_intr(math.floor, lc.INTR_FLOOR)
#unary_math_intr(math.ceil, lc.INTR_CEIL)
#unary_math_intr(math.trunc, lc.INTR_TRUNC)
unary_math_extern(math.log1p, "log1pf", "log1p")
if utils.PYVERSION > (2, 6):
    unary_math_extern(math.expm1, "expm1f", "expm1")
unary_math_extern(math.tan, "tanf", "tan")
unary_math_extern(math.asin, "asinf", "asin")
unary_math_extern(math.acos, "acosf", "acos")
unary_math_extern(math.atan, "atanf", "atan")
unary_math_extern(math.asinh, "asinhf", "asinh")
unary_math_extern(math.acosh, "acoshf", "acosh")
unary_math_extern(math.atanh, "atanhf", "atanh")
unary_math_extern(math.sinh, "sinhf", "sinh")
unary_math_extern(math.cosh, "coshf", "cosh")
unary_math_extern(math.tanh, "tanhf", "tanh")
unary_math_extern(math.ceil, "ceilf", "ceil")
unary_math_extern(math.floor, "floorf", "floor")
unary_math_extern(math.sqrt, "sqrtf", "sqrt")
unary_math_extern(math.trunc, "truncf", "trunc")


@register
@implement(math.isnan, types.float32)
def isnan_f32_impl(context, builder, sig, args):
    [val] = args
    return builder.not_(builder.fcmp(lc.FCMP_OEQ, val, val))


@register
@implement(math.isnan, types.float64)
def isnan_f64_impl(context, builder, sig, args):
    [val] = args
    return builder.not_(builder.fcmp(lc.FCMP_OEQ, val, val))


@register
@implement(math.isnan, types.int64)
def isnan_s64_impl(context, builder, sig, args):
    return cgutils.false_bit


@register
@implement(math.isnan, types.uint64)
def isnan_u64_impl(context, builder, sig, args):
    return cgutils.false_bit


POS_INF_F32 = lc.Constant.real(Type.float(), float("+inf"))
NEG_INF_F32 = lc.Constant.real(Type.float(), float("-inf"))

POS_INF_F64 = lc.Constant.real(Type.double(), float("+inf"))
NEG_INF_F64 = lc.Constant.real(Type.double(), float("-inf"))


@register
@implement(math.isinf, types.float32)
def isinf_f32_impl(context, builder, sig, args):
    [val] = args
    isposinf = builder.fcmp(lc.FCMP_OEQ, val, POS_INF_F32)
    isneginf = builder.fcmp(lc.FCMP_OEQ, val, NEG_INF_F32)
    return builder.or_(isposinf, isneginf)


@register
@implement(math.isinf, types.float64)
def isinf_f64_impl(context, builder, sig, args):
    [val] = args
    isposinf = builder.fcmp(lc.FCMP_OEQ, val, POS_INF_F64)
    isneginf = builder.fcmp(lc.FCMP_OEQ, val, NEG_INF_F64)
    return builder.or_(isposinf, isneginf)


@register
@implement(math.isinf, types.int64)
def isinf_s64_impl(context, builder, sig, args):
    return cgutils.false_bit


@register
@implement(math.isinf, types.uint64)
def isinf_u64_impl(context, builder, sig, args):
    return cgutils.false_bit


# -----------------------------------------------------------------------------


@register
@implement(math.atan2, types.int64, types.int64)
def atan2_s64_impl(context, builder, sig, args):
    [y, x] = args
    y = builder.sitofp(y, Type.double())
    x = builder.sitofp(x, Type.double())
    fsig = signature(types.float64, types.float64, types.float64)
    return atan2_f64_impl(context, builder, fsig, (y, x))

@register
@implement(math.atan2, types.uint64, types.uint64)
def atan2_u64_impl(context, builder, sig, args):
    [y, x] = args
    y = builder.uitofp(y, Type.double())
    x = builder.uitofp(x, Type.double())
    fsig = signature(types.float64, types.float64, types.float64)
    return atan2_f64_impl(context, builder, fsig, (y, x))


@register
@implement(math.atan2, types.float32, types.float32)
def atan2_f32_impl(context, builder, sig, args):
    assert len(args) == 2
    mod = cgutils.get_module(builder)
    fnty = Type.function(Type.float(), [Type.float(), Type.float()])
    fn = mod.get_or_insert_function(fnty, name="atan2f")
    return builder.call(fn, args)

@register
@implement(math.atan2, types.float64, types.float64)
def atan2_f64_impl(context, builder, sig, args):
    assert len(args) == 2
    mod = cgutils.get_module(builder)
    fnty = Type.function(Type.double(), [Type.double(), Type.double()])
    fn = mod.get_or_insert_function(fnty, name="atan2")
    return builder.call(fn, args)


# -----------------------------------------------------------------------------


@register
@implement(math.hypot, types.int64, types.int64)
def hypot_s64_impl(context, builder, sig, args):
    [x, y] = args
    y = builder.sitofp(y, Type.double())
    x = builder.sitofp(x, Type.double())
    fsig = signature(types.float64, types.float64, types.float64)
    return hypot_f64_impl(context, builder, fsig, (x, y))

@register
@implement(math.hypot, types.uint64, types.uint64)
def hypot_u64_impl(context, builder, sig, args):
    [x, y] = args
    y = builder.sitofp(y, Type.double())
    x = builder.sitofp(x, Type.double())
    fsig = signature(types.float64, types.float64, types.float64)
    return hypot_f64_impl(context, builder, fsig, (x, y))


@register
@implement(math.hypot, types.float32, types.float32)
def hypot_f32_impl(context, builder, sig, args):
    [x, y] = args
    xx = builder.fmul(x, x)
    yy = builder.fmul(y, y)
    sqrtsig = signature(sig.return_type, sig.args[0])
    sqrtimp = context.get_function(math.sqrt, sqrtsig)
    xxyy = builder.fadd(xx, yy)
    return sqrtimp(builder, [xxyy])


@register
@implement(math.hypot, types.float64, types.float64)
def hypot_f64_impl(context, builder, sig, args):
    [x, y] = args
    xx = builder.fmul(x, x)
    yy = builder.fmul(y, y)
    sqrtsig = signature(sig.return_type, sig.args[0])
    sqrtimp = context.get_function(math.sqrt, sqrtsig)
    xxyy = builder.fadd(xx, yy)
    return sqrtimp(builder, [xxyy])


# -----------------------------------------------------------------------------

@register
@implement(math.radians, types.float64)
def radians_f64_impl(context, builder, sig, args):
    [x] = args
    rate = builder.fdiv(x, context.get_constant(types.float64, 360))
    pi = context.get_constant(types.float64, math.pi)
    two = context.get_constant(types.float64, 2)
    twopi = builder.fmul(pi, two)
    return builder.fmul(rate, twopi)

@register
@implement(math.radians, types.float32)
def radians_f32_impl(context, builder, sig, args):
    [x] = args
    rate = builder.fdiv(x, context.get_constant(types.float32, 360))
    pi = context.get_constant(types.float32, math.pi)
    two = context.get_constant(types.float32, 2)
    twopi = builder.fmul(pi, two)
    return builder.fmul(rate, twopi)

unary_math_int_impl(math.radians, radians_f64_impl)

# -----------------------------------------------------------------------------

@register
@implement(math.degrees, types.float64)
def degrees_f64_impl(context, builder, sig, args):
    [x] = args
    full = context.get_constant(types.float64, 360)
    pi = context.get_constant(types.float64, math.pi)
    two = context.get_constant(types.float64, 2)
    twopi = builder.fmul(pi, two)
    return builder.fmul(builder.fdiv(x, twopi), full)

@register
@implement(math.degrees, types.float32)
def degrees_f32_impl(context, builder, sig, args):
    [x] = args
    full = context.get_constant(types.float32, 360)
    pi = context.get_constant(types.float32, math.pi)
    two = context.get_constant(types.float32, 2)
    twopi = builder.fmul(pi, two)
    return builder.fdiv(builder.fmul(x, full), twopi)

unary_math_int_impl(math.degrees, degrees_f64_impl)

# -----------------------------------------------------------------------------

@builtin_attr
@impl_attribute(types.Module(math), "pi", types.float64)
def math_pi_impl(context, builder, typ, value):
    return context.get_constant(types.float64, math.pi)

@builtin_attr
@impl_attribute(types.Module(math), "e", types.float64)
def math_e_impl(context, builder, typ, value):
    return context.get_constant(types.float64, math.e)
