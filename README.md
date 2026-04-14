# Ada Platform

Hub digital de projetos e arquivos para a Ada — uma intranet moderna e segura.

## Arquitetura

```
ada-platform/
├── backend/          # FastAPI + PostgreSQL + S3
│   ├── app/
│   │   ├── api/v1/routes/    # auth, users, content
│   │   ├── core/             # config, security, deps, exceptions
│   │   ├── db/               # engine, session
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── schemas/          # Pydantic DTOs
│   │   └── services/         # business logic
│   └── alembic/              # database migrations
└── frontend/         # React 18 + Vite + TypeScript
    └── src/
        ├── components/       # ui, layout, shared
        ├── pages/            # auth, dashboard, admin
        ├── services/         # API clients
        ├── store/            # Zustand auth state
        ├── hooks/            # custom hooks
        └── router/           # React Router + guards
```

## Stack

| Camada     | Tecnologia                                      |
|------------|-------------------------------------------------|
| Frontend   | React 18, Vite, TypeScript strict, ShadCN UI, Tailwind CSS, React Router v6, Zustand, TanStack Query v5, React Hook Form + Zod |
| Backend    | FastAPI, SQLAlchemy 2.0, PostgreSQL, Alembic, Pydantic v2, JWT, OAuth2 |
| Storage    | AWS S3                                          |
| Email      | Resend API                                      |

## Início Rápido

### 1. Pré-requisitos

- Docker e Docker Compose
- Node.js 20+
- Python 3.12+

### 2. Configuração

```bash
# Backend
cp backend/.env.example backend/.env
# Edite backend/.env com suas credenciais

# Frontend
cp frontend/.env.example frontend/.env
```

### 3. Docker Compose (recomendado)

```bash
docker compose up -d
```

Serviços disponíveis:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- Docs (Swagger): http://localhost:8000/docs
- PostgreSQL: localhost:5432

### 4. Rodar localmente (sem Docker)

**Backend:**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Criar banco e rodar migrations
alembic upgrade head

# Iniciar servidor
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Rotas da API

| Método | Rota                          | Descrição                        | Auth    |
|--------|-------------------------------|----------------------------------|---------|
| GET    | `/auth/google`                | Redirect para Google OAuth       | Público |
| GET    | `/auth/google/callback`       | Callback Google OAuth            | Público |
| POST   | `/auth/otp/request`           | Solicitar OTP por e-mail         | Público |
| POST   | `/auth/otp/verify`            | Verificar OTP e obter tokens     | Público |
| POST   | `/auth/refresh`               | Renovar access token             | Público |
| GET    | `/auth/me`                    | Dados do usuário autenticado     | Bearer  |
| GET    | `/users`                      | Listar usuários (paginado)       | Admin   |
| POST   | `/users`                      | Criar usuário                    | Admin   |
| GET    | `/users/:id`                  | Buscar usuário por ID            | Admin   |
| PATCH  | `/users/:id`                  | Atualizar usuário                | Admin   |
| DELETE | `/users/:id`                  | Soft delete de usuário           | Admin   |
| PATCH  | `/users/:id/activate`         | Ativar usuário                   | Admin   |
| PATCH  | `/users/:id/deactivate`       | Desativar usuário                | Admin   |
| GET    | `/content`                    | Listar conteúdos (paginado)      | Bearer  |
| POST   | `/content`                    | Criar conteúdo                   | Admin   |
| GET    | `/content/:id`                | Buscar conteúdo por ID           | Bearer  |
| PATCH  | `/content/:id`                | Atualizar conteúdo               | Admin   |
| DELETE | `/content/:id`                | Soft delete de conteúdo          | Admin   |
| POST   | `/content/upload`             | Upload HTML ou ZIP               | Admin   |
| GET    | `/content/:id/access`         | Obter URL de acesso              | Bearer  |
| GET    | `/content/:id/snippet`        | Gerar snippet JS                 | Admin   |

## Rotas do Frontend

| Rota                | Descrição                        | Auth         |
|---------------------|----------------------------------|--------------|
| `/login`            | Página de login                  | Público      |
| `/auth/google/callback` | Callback OAuth Google        | Público      |
| `/dashboard`        | Dashboard com grid de conteúdos  | Autenticado  |
| `/content/:id`      | Visualizador de conteúdo         | Autenticado  |
| `/admin`            | Visão geral administrativa       | Admin        |
| `/admin/users`      | Gestão de usuários               | Admin        |
| `/admin/content`    | Gestão de conteúdos              | Admin        |

## Modelo de Dados

### User
```
id, name, email, type (internal|external), role (admin|user),
auth_provider (google|otp), is_active, google_id, avatar_url,
otp_secret, otp_expires_at,
created_at, updated_at, deleted_at, is_deleted,
created_by, updated_by, deleted_by
```

### Content
```
id, title, description, type (project|file), icon, is_public,
external_url, file_type (html|zip|external), s3_path, uploaded_file_path,
created_at, updated_at, deleted_at, is_deleted,
created_by, updated_by, deleted_by
```

## Segurança

- Todos os endpoints protegidos validam JWT Bearer Token no backend
- Soft delete obrigatório — nunca DELETE físico
- Admin role validado no backend, nunca só no frontend
- OTP com expiração configurável (padrão 10 minutos)
- Refresh token automático via axios interceptor

## Upload de ZIP

1. Admin cria conteúdo do tipo `file` com `file_type: zip`
2. Admin faz upload do `.zip` via `/content/upload`
3. Backend valida existência de `index.html` no ZIP
4. Extrai e sobe todos os arquivos para `s3://bucket/content/{id}/`
5. Frontend abre `content/{id}/index.html` via iframe ou nova aba

## Snippet para Projetos Privados

Para projetos do tipo `project` com `is_public: false`, o admin pode gerar um snippet JS
via `/content/:id/snippet`. Este snippet deve ser inserido no `<head>` do projeto externo.

O snippet valida o JWT do usuário chamando a API `/content/:id/access`.
Caso inválido, redireciona para `/login` da plataforma Ada.
