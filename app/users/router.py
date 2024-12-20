from jose import jwt
from fastapi import APIRouter, HTTPException, status, Response, Depends, UploadFile, Request, File
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

from users.schemas import SUserRegister, STokens

from users.dao import UsersDAO
from users.auth import get_password_hash
from users.auth import authenticate_user, create_access_token
from users.schemas import SUserAuth
from users.models import User
from users.dependencies import get_current_user
from databases.schemas import NewDB
from config import get_auth_data

from databases.dao import DatabasesDAO

from users.auth import generate_single_part_token
from db_migration.migrate import DataMigration
import bleach
import requests
router = APIRouter(prefix='/user')
templates = Jinja2Templates(directory='templates')

@router.post("/register", tags=['Регистрация нового пользователя (номер телефона вводить в правильном виде)'], dependencies=[Depends(RateLimiter(times=2, seconds=1))])
async def register_user(user_data: SUserRegister, response: Response):
    user = await UsersDAO.find_one_or_none(email=user_data.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Пользователь с таким email уже существует')
    user_dict = user_data.dict()
    for i in user_dict.keys():
        user_dict[i] = bleach.clean(user_dict[i])
    user_dict['password'] = await get_password_hash(user_data.password)
    user_dict['tokens_count'] = 100
    user_dict['token'] = ''
    await UsersDAO.add(**user_dict)
    user = await UsersDAO.find_one_or_none(email=user_data.email)
    access_token = await create_access_token({"sub": str(user.id)})
    await UsersDAO.update(filter_by={'id': user.id}, token=access_token)
    response.set_cookie(key="users_access_token", value=access_token, httponly=True)
    return {"user_id": user.id, 'message':"ok"}


@router.get('/login', dependencies=[Depends(RateLimiter(times=5, seconds=1))])
async def get_students_html(request: Request):
    return templates.TemplateResponse(name='login.html', context={'request': request})

@router.post("/login", tags=['Авторизация пользователя'], dependencies=[Depends(RateLimiter(times=2, seconds=1))])
async def auth_user(response: Response, user_data: SUserAuth):
    check = await authenticate_user(email=user_data.email, password=user_data.password)
    if check is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Неверная почта или пароль')
    access_token = await create_access_token({"sub": str(check.id)})
    response.set_cookie(key="users_access_token", value=access_token, httponly=True)
    return {'access_token': access_token, 'refresh_token': None, 'message':"ok"}

@router.get("/profile", dependencies=[Depends(RateLimiter(times=3, seconds=1))])
async def get_me(request: Request, user_data: User = Depends(get_current_user)):
    if user_data is None:
        return RedirectResponse(url='/user/login')
    return templates.TemplateResponse(name='profile.html', context={'request': request, 'profile':user_data, "databases": await DatabasesDAO.find_all(user_token=user_data.token)})


@router.get("/buy_tokens", dependencies=[Depends(RateLimiter(times=5, seconds=1))])
async def buy_tokens_page(request: Request, user_data: User = Depends(get_current_user)):
    if user_data is None:
        return RedirectResponse(url='/user/login')
    return templates.TemplateResponse(name='buy_tokens.html', context={'request': request})

@router.put('/buy_tokens', tags=['Купить токены'], dependencies=[Depends(RateLimiter(times=3, seconds=1))])
async def buy_tokens(count: STokens, user_data: User = Depends(get_current_user)) -> dict:
    check = await UsersDAO.update(filter_by={'id': user_data.id},
                                   tokens_count=user_data.tokens_count+count.tokens)
    if check:
        return {"message": "Токены успешно добавлены!"}
    else:
        return {"message": "Ошибка при добавлении токенов"}

@router.get('/tokens_count',tags=['Запросить колво токенов'])
async def tokens_count(user_data: User = Depends(get_current_user)):
    if user_data is None:
        return RedirectResponse(url='/user/login')
    return user_data.tokens_count

@router.get('/token', tags=['Запросить свой токен'])
async def get_token(request: Request, user_data: User = Depends(get_current_user)):
    return user_data.token

@router.get('/projects', tags=['Запросить свои проекты'])
async def get_projects(user_data: User = Depends(get_current_user)):
    if user_data is None:
        return RedirectResponse(url='/user/login')
    return await DatabasesDAO.find_all(user_token=user_data.token)

@router.get('/new_project', dependencies=[Depends(RateLimiter(times=5, seconds=1))])
async def new_project_get(request: Request, user_data: User = Depends(get_current_user)):
    if user_data is None:
        return RedirectResponse(url='/user/login')
    return templates.TemplateResponse(name='new_project.html', context={'request': request})

@router.post("/new_project", tags=['Создать новый проект'], dependencies=[Depends(RateLimiter(times=1, seconds=10))])
async def db_connect(db_info: NewDB, user_data: User = Depends(get_current_user)):
    db_dict = db_info.dict()
    for i in db_dict.keys():
        db_dict[i] = bleach.clean(db_dict[i])
    db_dict['user_token'] = user_data.token
    db_dict['token'] = ''
    db_dict['metadata_columns'] = db_info.metadata_columns.split()
    await DatabasesDAO.add(**db_dict)
    db = (await DatabasesDAO.find_all(user_token=user_data.token))[-1]
    db_token = generate_single_part_token(db.id)
    await DatabasesDAO.update(filter_by={'id': db.id},token=db_token)
    await UsersDAO.update(filter_by={'id': user_data.id}, databases=user_data.databases+[db_token])
    config = {
        'database': {
            'dialect': db.dialect,  # Тип реляционной базы данных (может быть MySQL, SQLite, etc.)
            'host': db.host,  # Хост базы данных
            'port': int(db.port),  # Порт базы данных
            'user': db.user,  # Имя пользователя для базы данных
            'password': db.password,  # Пароль для подключения к базе данных
            'database': db.db_name  # Название базы данных
        },
        'qdrant': {
            'host': '87.249.44.115',  # Хост для подключения к Qdrant
            'port': 6333,  # Порт для подключения к Qdrant
            'collection_name': db_token,  # Имя коллекции в Qdrant
            'vector_size': 1024  # Размер векторов (должен соответствовать модели)
        },
        'mapping': {
            'table': db.table_name,  # Имя таблицы в реляционной базе данных
            'vector_column': db.vector_column,  # Колонка с текстом для векторизации
            'image_column': db.image_column,
            'metadata_columns': db.metadata_columns,  # Колонки с метаданными
        },
        'image_save_path': './images',  # Директория для сохранения изображений
        'lang': 'en'  # Язык
    }
    try:
        migrator = DataMigration(config)
        migrator.migrate()
    except:
        return {'message':'Ошибка'}
    return {'message':"OK"}

@router.get('/bot_info/{id}', dependencies=[Depends(RateLimiter(times=5, seconds=1))])
async def bot_info(id:int, request: Request, user_data: User = Depends(get_current_user)):
    if user_data is None:
        return RedirectResponse(url='/user/login')
    return templates.TemplateResponse(name='bot_info.html', context={'request': request, 'db': await DatabasesDAO.find_one_or_none_by_id(id)})
