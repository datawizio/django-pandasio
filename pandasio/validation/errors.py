from abc import abstractmethod
from dataclasses import dataclass, field
from typing import ClassVar, List, Any, Optional, Tuple, Union

import pandas as pd
from . import validators


@dataclass
class Error:
    CODE: ClassVar[Optional[str]] = None

    def __post_init__(self):
        assert self.CODE is not None, "`CODE` cannot be None."
        assert self.CODE.isupper(), "The `CODE` should be uppercase."

    @abstractmethod
    def to_dict(self, s: Optional[pd.Series], *args: Any, **kwargs: Any) -> dict:
        pass

    def form_response(self, s: Optional[pd.Series], **kwargs: Any) -> dict:
        return {
            "reason": self.CODE,
            "indexes": list(s.index.values) if s is not None else [],
            **kwargs,
        }


@dataclass
class FieldValidationErrorManager:
    errors: List[dict] = field(init=False, default_factory=list)

    def log_error(self, error: Error, s: Optional[pd.Series]) -> None:
        self.errors.append(error.to_dict(s))

    def log_validator_error(self, validator: "validators.BaseValidator", s: Union[pd.Series, pd.DataFrame]) -> None:
        result = {}
        if isinstance(validator, validators.MinValueValidator):
            result = MinValueError(min_value=validator.limit_value).to_dict(s)
        elif isinstance(validator, validators.MaxValueValidator):
            result = MaxValueError(max_value=validator.limit_value).to_dict(s)
        elif isinstance(validator, validators.MinLengthValidator):
            result = MinLengthError(min_value=validator.limit_value).to_dict(s)
        elif isinstance(validator, validators.MaxLengthValidator):
            result = MaxLengthError(max_value=validator.limit_value).to_dict(s)
        elif isinstance(validator, validators.UniqueTogetherValidator):
            result = NonUniqueTogetherError(unique_together_fields=validator.limit_value).to_dict(s)
        else:
            raise NotImplementedError(f"Support for `{validator.__class__.__name__}` validator not implemented yet.")
        self.errors.append(result)


@dataclass
class NonNumericValueError(Error):
    CODE = "NON_NUMERIC_VALUE"

    def to_dict(self, s: Optional[pd.Series], *args: Any, **kwargs: Any) -> dict:
        return self.form_response(
            s=s.loc[s.apply(lambda x: not str(x).lstrip("-").isnumeric())].dropna()
        )


@dataclass
class FieldRequiredError(Error):
    CODE = "FIELD_REQUIRED"

    def to_dict(self, s: Optional[pd.Series], *args: Any, **kwargs: Any) -> dict:
        return self.form_response(s=None)


@dataclass
class NullNotAllowedError(Error):
    CODE = "NULL_NOT_ALLOWED"

    def to_dict(self, s: Optional[pd.Series], *args: Any, **kwargs: Any) -> dict:
        return self.form_response(s=s[s.isnull()])


@dataclass
class MinValueError(Error):
    CODE = "MIN_VALUE"
    min_value: int

    def to_dict(self, s: Optional[pd.Series], *args: Any, **kwargs: Any) -> dict:
        return self.form_response(s=s.loc[s < self.min_value], limit_value=self.min_value)


@dataclass
class MaxValueError(Error):
    CODE = "MAX_VALUE"
    max_value: int

    def to_dict(self, s: Optional[pd.Series], *args: Any, **kwargs: Any) -> dict:
        return self.form_response(s=s.loc[s > self.max_value], limit_value=self.max_value)


@dataclass
class MinLengthError(Error):
    CODE = "MIN_LENGTH_VALUE"
    min_value: int

    def to_dict(self, s: Optional[pd.Series], *args: Any, **kwargs: Any) -> dict:
        return self.form_response(s=s.loc[s.str.len() < self.min_value], limit_value=self.min_value)


@dataclass
class MaxLengthError(Error):
    CODE = "MAX_LENGTH_VALUE"
    max_value: int

    def to_dict(self, s: Optional[pd.Series], *args: Any, **kwargs: Any) -> dict:
        return self.form_response(s=s.loc[s.str.len() > self.max_value], limit_value=self.max_value)


@dataclass
class NonUniqueTogetherError(Error):
    CODE = "NON_UNIQUE_TOGETHER"
    unique_together_fields: List[str]

    def to_dict(self, s: pd.DataFrame, *args: Any, **kwargs: Any) -> dict:
        return self.form_response(
            s=s[s.duplicated(subset=self.unique_together_fields)],
            unique_together_fields=self.unique_together_fields,
        )


@dataclass
class IncorrectDateFormatError(Error):
    CODE = "INCORRECT_DATE_FORMAT"
    format: str

    def to_dict(self, s: Optional[pd.Series], *args: Any, **kwargs: Any) -> dict:
        s = pd.to_datetime(s, format=self.format, errors="coerce").dt.date
        return self.form_response(
            s=s[s.apply(lambda x: x is pd.NaT)],
            format=self.format
        )


@dataclass
class IncorrectDateTimeFormatError(IncorrectDateFormatError):
    CODE = "INCORRECT_DATETIME_FORMAT"


@dataclass
class ImageFormatNotSupportedError(Error):
    CODE = "IMAGE_FORMAT_NOT_SUPPORTED"
    supported_extensions: Tuple[str, ...]

    def to_dict(self, s: Optional[pd.Series], *args: Any, **kwargs: Any) -> dict:
        return self.form_response(
            s=s[~s],  # False when extensions is not supported
            supported_extensions=self.supported_extensions,
        )


@dataclass
class IdentifierNotFoundError(Error):
    CODE = "IDENTIFIER_NOT_FOUND"

    def to_dict(self, s: Optional[pd.Series], *args: Any, **kwargs: Any) -> dict:
        return self.form_response(s=s)


@dataclass
class BlankNotAllowed(Error):
    CODE = "BLANK_NOT_ALLOWED"

    def to_dict(self, s: Optional[pd.Series], *args: Any, **kwargs: Any) -> dict:
        return self.form_response(s=s.loc[s == ''])
