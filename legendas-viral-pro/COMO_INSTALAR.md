# Como Instalar

## 1. Pasta do plugin

Copie a pasta `legendas-viral-pro` para uma destas pastas CEP:

### Instalação por usuário

```powershell
%APPDATA%\Adobe\CEP\extensions\Legendas Viral Pro
```

### Instalação global

```powershell
C:\Program Files (x86)\Common Files\Adobe\CEP\extensions\Legendas Viral Pro
```

Recomendo a instalação por usuário durante desenvolvimento.

## 2. Habilitar extensões CEP sem assinatura

Em ambiente de desenvolvimento, o Adobe pode bloquear extensões sem assinatura. Ative o modo debug CEP no Registro do Windows:

```powershell
reg add HKCU\Software\Adobe\CSXS.11 /v PlayerDebugMode /t REG_SZ /d 1 /f
reg add HKCU\Software\Adobe\CSXS.12 /v PlayerDebugMode /t REG_SZ /d 1 /f
```

## 3. Abrir no Adobe

Reinicie o Premiere Pro ou After Effects e abra:

```text
Janela > Extensões > Legendas Viral Pro
```

## 4. Adicionar modelos

Coloque modelos nas pastas:

- `templates/1-linha`
- `templates/2-linhas`
- `templates/3-linhas`
- `templates/4-linhas`
- `templates/5-linhas`

Formatos aceitos pelo painel: `.mogrt`, `.cgt`, `.cga`, `.aep`.

## Observação importante

O plugin novo não altera o `Legendas Master 3.7`. Ele fica em pasta separada, com outro Bundle ID:

```text
com.josevictor.legendasviralpro
```
