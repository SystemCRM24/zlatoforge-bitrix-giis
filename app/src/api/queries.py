from fastapi import Query


ContactIDQuery = Query(description="ИД контакта клиента в битриксе.")

UserIDQuery = Query(
    description="ИД пользователя, которому будет отправлено уведомление.", default="7780"
)

ContourTypeQuery = Query()
