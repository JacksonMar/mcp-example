"""Input models for signup and signin. No network, no MCP."""

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class SignUpInput(BaseModel):
    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True)

    name: str = Field(min_length=2, max_length=20)
    last_name: str = Field(alias="lastName", min_length=2, max_length=20)
    email: str
    password: str = Field(min_length=8, max_length=15)
    repeat_password: str = Field(alias="repeatPassword")

    @field_validator("password")
    @classmethod
    def check_password(cls, value: str) -> str:
        if not any(c.isupper() for c in value):
            raise ValueError("password must contain an uppercase letter")
        if not any(c.islower() for c in value):
            raise ValueError("password must contain a lowercase letter")
        if not any(c.isdigit() for c in value):
            raise ValueError("password must contain a digit")
        return value

    @model_validator(mode="after")
    def check_passwords_match(self) -> "SignUpInput":
        if self.repeat_password != self.password:
            raise ValueError("repeatPassword must be equal to password")
        return self

    def to_payload(self) -> dict[str, str]:
        return self.model_dump(by_alias=True)


class SignInInput(BaseModel):
    email: str = Field(min_length=3)
    password: str = Field(min_length=8, max_length=15)

    def to_payload(self) -> dict[str, str]:
        return self.model_dump()
