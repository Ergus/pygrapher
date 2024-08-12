# Fundamentals of Floating-Point Arithmetic

## Numerical Representation

- Floating-point numbers are representations expressed through an exponential operation.
- Modern floating-point representation is standardized by [IEEE
  754](https://en.wikipedia.org/wiki/IEEE_754).
- The standard defines 5 basic types of floating-point numbers. However, in our code, we typically
  only use `float` (32 bits) and `double` (64 bits).
- Significant digits limits precision in this representation.
  - `float`: 6-7.
  - `double`: 15-16.
- The bounds of absolute error are limited by the represented value due to above.
- But the relative error associated with the representation is of constant order.
- The base of the number in binary (mantissa) determines the precision with which it is possible to
  represent it.
- Some values are perfectly representable in the IEEE 754 format (for example, 0.25, 2.0, 1.75,
  3.5).
- But most numbers are approximated by rounding or truncating the mantissa.
- The "amount" of consecutive floating-point numbers decreases for values further from zero (as a
  consequence of the binary exponential representation).
- The rounding method is not standard, so each compiler may use a different strategy. (Microsoft's
  compiler generally truncates, while gcc rounds)
- Useful resources for viewing the representation of a number and its implicit error:
  - [Converter](https://www.h-schmidt.net/FloatConverter/IEEE754.html
    "IEEE-754 Floating Point Converter"),
  - [Representation](https://www.binaryconvert.com/result_double.html)
- Intel processors execute most floating-point operations in extended precision (80 bits), but that
  may be insufficient when the input values was truncated in previous operations.

## Sources of Errors and Variations

- It is as important to determine a value as its associated error (or error bound).
- The first sources of error in numerical computation are the rounding and truncation of number
  representations.
- This error affects final results as well as intermediate values of calculations.
- Truncation and round error should be treated as an experimental error (with the same nature as
  precision or instrumental error).
- The most efficient types for floating-point computation in modern architectures are `float` and
  `double`.
- However, sometimes it may be necessary to use larger types to store intermediate values (e.g.,
  `long double`).
  - Use [double-double
    arithmetic](https://en.wikipedia.org/wiki/Quadruple-precision_floating-point_format#Double-double_arithmetic)
    computation.
  - Use [libquadmath](https://gcc.gnu.org/onlinedocs/libquadmath/) provided by gcc.
  - Use [Boost multiprecision](https://www.boost.org/doc/libs/1_80_0/libs/multiprecision/doc/html/index.html)
- Larger types impact the efficiency of an operation, so their use should be strictly limited to
  necessary cases.
- Mathematical libraries use two types of approximations to perform basic operations.
- Therefore, the same calculation may not be deterministic/reproducible across different systems,
  compilers, or libraries (even versions of the same library).
  1. Hardware approximations (intrinsics: `_mm_pow_pd`, `_mm_exp_pd`,
     `_mm_exp10_pd`) [Intel Intrinsics
     Guide](https://www.intel.com/content/www/us/en/docs/intrinsics-guide/index.html)
  2. Software approximations (Pade Approximation, Taylor Method)
     [Cephes
     Library](https://github.com/jeremybarnes/cephes/tree/master/cmath),
     [fastermath](https://github.com/akohlmey/fastermath/tree/master/src)
- Intel architectures include (at the hardware level) several
  instructions for the same approximation/operation.
  - Some approximations guarantee total coincidence up to the 14th digit in `double`.
  - Some instructions associated with mathematical operations prioritize performance over precision.
  - The instructions used in the final code will depend on the compiler, optimization flags, and
    even the order of operations and memory access.
  - For example, vectorizable code may use SSE or AVX. [Vectorization
    Guide](https://www.intel.com/content/dam/develop/external/us/en/documents/31848-compilerautovectorizationguide.pdf)
- The associated error for software-based approximations is expressed in terms of ULP (units of
  least precision).
  - For the glibc library, the ULP of each operation is documented at: [glibc float
    Error](https://www.gnu.org/software/libc/manual/html_node/Errors-in-Math-Functions.html)
- The most sensitive functions to variations are usually the exponential family.
- The largest errors usually occur when operations with large modulus numbers return small
  results. This is due to the thinning of floating-point numbers for values far from
  zero. [Precision](https://learn.microsoft.com/en-us/cpp/build/why-floating-point-numbers-may-lose-precision)

## Error Propagation

- Our error-checking system uses both absolute and relative errors.
- A correct estimation of error bounds defines the viability of an implementation and the
  reliability of the results.
- Since computers are unaware of their own numerical limitations in operations, error bound
  estimation is the EXCLUSIVE task of the programmer.
  - It is enough to avoid certain (anti)patterns and/or assume the worst-case scenario in order to
    avoid increasing the cost of error estimation too much.
- Never express the error with more than two digits.
  - Therefore, the tolerance should never be less than the second digit of the error.
- The absolute error value for a derived variable includes the error's propagation from all
  variables involved in obtaining it.

	The first approximation is usually the summation of the partial
     differentials with respect to each of those variables.

	$$\Delta A = \sum_i{\frac{\partial A}{\partial x_i} \Delta x_i}$$

	where $x_i$ represents each of the approximated variables involved
     in the calculation of $A$ and $\Delta x_i$ their known/estimated
     error bound.

- For common operations, conventional absolute and relative error formulas are well-determined:
  [Error Propagation](https://www.uv.es/zuniga/3.2_Propagacion_de_errores.pdf),
  [Error Propagation formulas](https://www.mariogonzalez.es/files/111006-propagacion.pdf).
  - $\Delta (A \pm B) = \Delta A + \Delta B$
  - $\Delta (A * B) = \Delta A * B + A * \Delta B$
  - $\Delta \frac{A}{B} = \frac{\Delta A * B + A * \Delta B}{B^2}$
  - $\Delta A^n = |n| A^{n - 1} \Delta A \equiv |n|\frac{\Delta A}{A} A^n$
  - $\Delta C^A = C^A * \Delta A \ln(C)$
- Three very common patterns in numerical analysis arise from the very formulation of errors. These
  are particularly susceptible to precision errors as a consequence of rounding:
  - Perturbations: Calculations of small differences between similar values (e.g., a base value and
    one estimated by different means).

    If $a \simeq a'$ then trom the previous error formula $a - a' \ll a$ as $\Delta (a - a') =
    \Delta a + \Delta a'$ it is then quite frequent that the relative error of the difference is
    amplified several orders of magnitude than the initial relative error of $a$ and
    $a'$ . [Catastrophic cancellation](https://en.wikipedia.org/wiki/Catastrophic_cancellation)

  - Reductions: Summing many floating-point numbers (generally in a vector).

    When an initial value can be expressed as: $\sum_i A_i$ the final
    error can be expressed as $\sum_i |\Delta A_i|$ .

    This simple case adds two additional problems.

    1. If there are pairs of similar values of opposite sign, the scenario of [Catastrophic
       cancellation](https://en.wikipedia.org/wiki/Catastrophic_cancellation) repeats.

    2. If consecutive values are very different (in orders of magnitude), the mantissas of the large
       numbers cancel out those of the small numbers.

  - Accumulations: Similar to the previous case, but the values are summed accumulatively in loops.

    This specific case is enumerated separately because pre-ordering is not applicable. Sometimes it
    is necessary to modify the implementation to a reduction problem.

- The correct implementation of a numerical formula requires meeting the three criteria of
  [Hadamard](https://www.statisticshowto.com/well-posed-ill/). The third criterion is the most
  difficult to corroborate in most situations.
  - Operations like `ceil`, `round`, or `trunc` do not meet this criterion by definition; and their
    use requires special attention. For example: `size_t n = std::ceil(size / step)` can produce
    variations of $\pm 1$ for step variations of any order, even below the accepted
    tolerance. Although this operation is often used in situations where an increased number of
    steps does not affect the validity of the approximation (e.g., numerical integration). The
    variation in the result can be orders of magnitude greater than the tolerance.
  - Operations like `exp`, `exp2`, `pow` could produce significant perturbations in the result
    although they meet the criterion in most of their domain.

- Numerical instabilities usually manifest themselves in certain region of the function domain only
  or ill-posed problems.

  - For example, the `exp` function is quite imprecise for $x$ near zero, and many formulas use
    `exp(x) - 1`. In that case, using `expm1` solves the precision problem. Something similar
    happens with `log` and `log1p`.

  Another example of transforming a problem: [Minimizing the effect of accuracy
  problems](https://en.wikipedia.org/wiki/Floating-point_arithmetic#Minimizing_the_effect_of_accuracy_problems)

## Patterns and Anti-Patterns

Although precision errors cannot be completely avoided, there is a set of recommendations (best
practices) that are particularly relevant in floating-point numerical code. Here are some of the
most common:

### Catastrophic Cancellation

- Catastrophic cancellation [Catastrophic
  cancellation](https://en.wikipedia.org/wiki/Catastrophic_cancellation) is the **most frequent**
  problem in numerical code and has already been described earlier in the section on perturbations.

- Although it is very difficult to avoid it entirely, it is possible to reduce its effects.

    1. Rescaling numbers before performing subtraction (for example: multiplying them by a number
       that brings them closer to zero).
    2. Postponing operations (for example: factoring out common terms before subtraction if
       possible).
       $1000 * x - 1000 * y \Rightarrow  1000 * (x - y)$
    3. Avoiding divergent operations (such as `exp` or `pow` if $x > 1$) if possible and replacing
       them with convergent operations (`log`, `sqrt`) if the formulation allows.

Remember that the most important thing in this scenario is to make a realistic estimate of the final
absolute error in the subtraction and ensure that the relative value is 

The [Sterbenz Lemma](https://en.wikipedia.org/wiki/Sterbenz_lemma) is very useful tool to get error
bounds theorems in numerical analysis.


### Avoiding Unnecessary Accumulations for Fixed Ranges

```C
// Don't
for (double x = start; x < end; x+= step)
{
    // store or use x
}
```

This code, although simple, has the drawback that each addition to the variable `x` accumulates a
rounding error associated with the sum. This rounding depends exclusively on the representability of
the values taken by `x`.

One way to avoid this is by using a fixed origin and avoiding interdependencies:

```C
// Do
size_t nsteps = (end - start) / step;
for (size_t i = 0; i < nsteps; ++i)
{
    x = start + step * i;
    // store or use x
}
```

Note: This code seems more costly because it replaces 1 addition with a multiplication. However, it
is a necessary trade-off. Additionally, the new code eliminates inter-dependencies between loops,
which allow the compiler to vectorize under certain conditions.

### Reduction

```C
// Don't
double sum = 0;
for (double var : myvector)
{
    sum += var;
}
```

To avoid the issue of summing large numbers with small ones and the cancellation of significant
digits, there are two possible alternatives to the above code:

1. Pre-ordered Reduction: This involves sorting the values in the vector before summing them. The
   sorting should be done in a modular fashion, grouping positive and negative values
   separately. Then, sum starting from the values closest to zero.

   ```C
   // Do
   double preorderedSum(vector<double> A) // pass vector by value to make a copy and work on it
   {
       std::sort(A.begin(), A.end());
       return std::reduce(A.begin(), A.end());
   }
   ```

   Note: The initial method has a complexity of $O(n)$ . However, sorting has a complexity of $O(n
   log(n)) + O(n)$ . This is especially recommended when there are many small values and a few large
   ones.

   The example above assumes a vector with only positive values.

   The `std::reduce` function already performs the sum by consecutive pairs (binary reduction).

2. Use the [Kahan Summation
   Algorithm](https://en.wikipedia.org/wiki/Kahan_summation_algorithm)

	```C
    // Do
	double kahanSum(const vector<double> &A)
	{
	    double sum = 0.0, c = 0.0; // c will store the error

	    // Loop to iterate over the array
	    for (double val : A)
	    {
	        double y = val - c;
	        double t = sum + y;

	        c = (t - sum) - y;
	        sum = t;
	    }
	    return sum;
	}
	```

   Note: This method can be silently invalidated by excessive compiler optimizations:
   [See](https://en.wikipedia.org/wiki/Kahan_summation_algorithm#Possible_invalidation_by_compiler_optimization)

3. Compute the round-off error with the [2sum algorithm](https://en.wikipedia.org/wiki/2Sum)

### Horner's Method

This simple algorithm is a way to avoid excessive accumulation and interdependencies in polynomial
calculations. This method has the dual advantage of reducing the number of multiplications by almost
half while also reducing rounding errors. [Horner's
Method](https://juncotic.com/metodo-de-horner-algoritmos-antiguos/)

$$ aX^n + bX^{n-1} + cX^{n-2} + \dots \equiv ((aX + b)X + c)X + \dots$$

```C
// Do
int HornerEvaluate(const std::vector<double> &coefs, double valueX)
{
    double result = 0;

    for(double coef : coefs)
        result = result * valueX + coef;

    return result;
}
```

### Premature Rounding

Premature rounding is a technique that requires careful application. It involves simply eliminating
non-significant digits below a known error after expansion.

For example, in the case of a value $3.1425926536 \pm 0.0015$, the simplest way to avoid numerical
oscillations in subsequent calculations is to round the value to: $3.1415000000 \pm 0.0025$ . Values
after fifth digit are smaller than the error and only add noise.

### Comparisons

In the code:

```C
// Don't
if (mydouble < 0.0) {}
if (mydouble == othervalue) {}
```

Comparisons need to consider the numerical tolerance of myvalue; or even its error bound if it is a
value derived from previous operations. Failing to do so can lead to underestimating our error and
making completely incorrect assessments.

In general:
    The `==` operator should be NEVER used with floating-point numbers (except, perhaps, to compare initialized and unmodified values).

```C
// Do
if (mydouble < tolerance) {}
if (abs(mydouble - othervalue) < tolerance) {}
```

where `tolerance` is obviously a positive value.

This method is of greater importance when non-contiguous functions like `ceil`, `round`, or `trunc`
are involved.

### Other Recommendations

- Most mathematical libraries, such as [Eigen](https://eigen.tuxfamily.org/index.php), already
  incorporate these principles (or are consistent in their handling). They report errors bounds
  associated with the results (or provide tools to do it efficiently); but can also detect errors in
  the input data and report the error before returning a silently incorrect result. Therefore, using
  such libraries is highly recommended.

  There are many algorithms in `Mathtools` that are already provided by standard numerical libraries
  (i.e. linear solvers, decomposition, Least Squares). The versions in libraries like Eigen , MKL or
  Blass are extensively tested, optimized and include numerical stabilization strategies when
  needed. So, please, consider the migration to one of the standard implementations and avoid the
  *made in home* syndrome.

- The test suite should include unit tests and integration tests. Both types of tests should use
  realistic tolerances based on actual errors.

  Most of our tests are integration tests that underestimate rounding errors while increasing them
  due to the large number of calculation steps and operations
  involved. [See](https://jesuslc.com/2023/12/02/la-piramide-del-testing/)

- C++ provides numeric constants and accuracy limits in the
  [<limits>](https://en.cppreference.com/w/cpp/types/numeric_limits) library. Those are better
  alternatives to old C macro constants.

[1] <https://docs.oracle.com/cd/E19957-01/806-3568/ncg_goldberg.html>

[2] <https://en.wikipedia.org/wiki/Floating-point_arithmetic>
