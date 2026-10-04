---
name: module-pattern
description: How a module and its test are laid out in this Python service (src layout, mypy strict, pytest), with the code each starts from. Read before you add a module or a package.
---
# The module pattern

Code lives in `src/<package>/` (snake_case, with an `__init__.py`); tests in `tests/` as
`test_<module>.py`. Every behaviour you add has a test. mypy runs in strict mode over `src` and
`tests`.

```
src/coat_api/
  __init__.py
  py.typed
  pricing.py
tests/
  test_pricing.py
```

## A module

```python
"""Prices for coating jobs."""

from dataclasses import dataclass


class PricingError(ValueError):
    """The job can't be priced."""


@dataclass(frozen=True)
class Job:
    area_m2: float
    layers: int = 1


def price(job: Job, rate_per_m2: float) -> float:
    """The price of a job; raises PricingError for an empty one."""
    if job.area_m2 <= 0 or job.layers < 1:
        raise PricingError(f"nothing to coat: {job}")
    return round(job.area_m2 * job.layers * rate_per_m2, 2)
```

What the checks hold you to:

- **Type everything**: parameters, returns, attributes. No implicit `Any`: `dict[str, int]`, not
  `dict`. A function that returns nothing says `-> None`.
- **Specific exceptions.** Raise your own (subclassing a built-in) or a fitting built-in; never
  catch with a bare `except:`. Catch what you can handle, and name it.
- **No mutable defaults** (`def f(items: list[str] = [])`): use `None` and create inside, or a
  dataclass `field(default_factory=list)`.
- **Small functions, data in dataclasses** (frozen when they're values).
- **Imports**: standard library, third party, then your package, each block sorted; ruff does
  it for you. Import your own code absolutely: `from coat_api.pricing import price`.
- Unused code is reported (as a warning): delete what nothing calls.

## Its test

```python
import pytest

from coat_api.pricing import Job, PricingError, price


def test_price_multiplies_area_layers_and_rate() -> None:
    assert price(Job(area_m2=2.5, layers=2), rate_per_m2=10.0) == 50.0


@pytest.mark.parametrize("job", [Job(area_m2=0), Job(area_m2=1, layers=0)])
def test_an_empty_job_cannot_be_priced(job: Job) -> None:
    with pytest.raises(PricingError):
        price(job, rate_per_m2=10.0)
```

- Tests are typed too (`-> None`, typed parameters): mypy checks `tests/`.
- Plain `assert`; `pytest.raises` for errors; `parametrize` for tables of cases.
- One test file per module, named after it: a new `pricing.py` gets `tests/test_pricing.py`
  (plan mode checks that it's planned).
- Test behaviour through the module's public functions, not its private helpers.

## A new package

A folder under `src/` needs an `__init__.py` and a snake_case name, or the structure check
refuses it. Keep `__init__.py` to what the package offers (`from coat_api.pricing import price`
and an `__all__`), no logic.

## Running what the checks run

```
.venv/bin/ruff check src tests
.venv/bin/mypy --output json src tests
.venv/bin/pytest -q
```

Formatting is applied for you after your pass; don't spend turns on it. A new dependency
(`uv add`) needs the human's confirmation: do without, or name it in your open issues.
