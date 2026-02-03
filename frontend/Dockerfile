# Этап сборки
FROM node:18-alpine AS builder

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей
COPY package*.json ./

# Устанавливаем зависимости
RUN npm install

# Копируем исходный код
COPY . .

# API URL для сборки (передается через Build Arguments в Northflank)
ARG VITE_API_URL=https://p01--lightnovelnlp--95w5j7vcjd9s.code.run
ENV VITE_API_URL=$VITE_API_URL

# Собираем приложение
RUN npm run build

# Этап продакшена
FROM nginx:alpine

# Копируем собранные файлы
COPY --from=builder /app/dist /usr/share/nginx/html

# Копируем конфигурацию nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Открываем порт
EXPOSE 8080

# Запускаем nginx
CMD ["nginx", "-g", "daemon off;"]
