from django.contrib.auth.models import AbstractUser, Group, Permission, User
from django.conf import settings
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField



# Tabela preenchida manualmente utilizando uma query gerada pelo Excel com os proóximos jogos
class Proximos_jogos(models.Model):
    game_id = models.IntegerField(unique=True) 
    data = models.DateField()
    hora = models.TimeField()
    campeonato = models.CharField(max_length=100)
    time_casa = models.CharField(max_length=100)
    time_visitante = models.CharField(max_length=100)
    casasApostasOdds_time_casa = models.DecimalField(max_digits=5, decimal_places=2)
    casasApostasOdds_empate = models.DecimalField(max_digits=5, decimal_places=2)
    casasApostasOdds_time_visitante = models.DecimalField(max_digits=5, decimal_places=2)
    
    def apostas_time_casa(self):
        return self.aposta_set.filter(time=self.time_casa)

    def apostas_time_visitante(self):
        return self.aposta_set.filter(time=self.time_visitante)


# Tabela preenchida manualmente utilizando uma query gerada pelo Excel com os jogos que já aconteceram.
class Jogos(models.Model):
    game_id = models.IntegerField(unique=True) 
    data = models.DateField()
    hora = models.TimeField()
    campeonato = models.CharField(max_length=100)
    time_casa = models.CharField(max_length=100)
    time_visitante = models.CharField(max_length=100)
    casasApostasOdds_time_casa = models.DecimalField(max_digits=5, decimal_places=2)
    casasApostasOdds_empate = models.DecimalField(max_digits=5, decimal_places=2)
    casasApostasOdds_time_visitante = models.DecimalField(max_digits=5, decimal_places=2)
    pontuacaoGuessGame_time_casa = models.FloatField(null=True, blank=True) # Pontuação prevista pela Guess-Game
    pontuacaoGuessGame_time_visitante = models.FloatField(null=True, blank=True) # Pontuação prevista pela Guess-Game 

    def apostas_time_casa(self):
        return self.aposta_set.filter(time=self.time_casa)

    def apostas_time_visitante(self):
        return self.aposta_set.filter(time=self.time_visitante)


# Tabela preenchida manualmente utilizando uma query gerada pelo Excel com os resultados dos jogos.
class ResultadoJogo(models.Model):
    jogo = models.ForeignKey(Jogos, on_delete=models.CASCADE, to_field='game_id', related_name='resultados_jogo')
    resultado_time_casa = models.IntegerField()
    resultado_time_visitante = models.IntegerField()

    def __str__(self):
        return f"Resultado de {self.jogo}"


# Tabela atualizada automaticamente pela função atualizar_apostas no utils.py e de acordo com a class Jogos/ResultadoJogo,
# utiliza-se o comands no terminal: python manage.py atuApostas 
class Aposta(models.Model):
    jogo = models.ForeignKey(Jogos, on_delete=models.CASCADE, to_field='game_id')
    data = models.DateField()
    hora = models.TimeField()
    campeonato = models.CharField(max_length=100)
    time = models.CharField(max_length=100)
    qtde_jogos = models.IntegerField(default=0)
    pontos = models.IntegerField(default=0)
    vitorias = models.IntegerField(default=0)
    empates = models.IntegerField(default=0)
    derrotas = models.IntegerField(default=0)
    gols_marcados = models.IntegerField(default=0)
    gols_contra = models.IntegerField(default=0)
    gols_saldo = models.IntegerField(default=0)
    casasApostasOdds_acertos = models.IntegerField(default=0)
    guessGameOdds_acertos = models.IntegerField(default=0)
    zebra = models.IntegerField(default=0)
    vitorias_casa = models.IntegerField(default=0)
    vitorias_fora = models.IntegerField(default=0)
    empates_casa = models.IntegerField(default=0)
    empates_fora = models.IntegerField(default=0)
    derrotas_casa = models.IntegerField(default=0) 
    derrotas_fora = models.IntegerField(default=0)
    favorito_empate = models.IntegerField(default=0)
    favorito_derrota = models.IntegerField(default=0)

    def __str__(self):
        return f"Aposta realizada de {self.jogo}"



# Tabela atualizada automaticamente pela função atualizar_pesos no utils.py e de acordo com a class DesempenhTime (Aposta),
# utiliza-se o comands no terminal: python manage.py atuPesos
class Pesos(models.Model):
    campeonato = models.CharField(max_length=100)
    time = models.CharField(max_length=100)
    pontos = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    gols_marcados = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    gols_contra = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    gols_saldo = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    vitorias = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    empates = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    derrotas = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    def __str__(self):
        return self.jogo


# Tabela atualizada automaticamente pela função atualizar_pontos no utils.py e de acordo com a class Pesos,
# utiliza-se o comands no terminal: python manage.py atuPontos
# Esse arquivo deve ser exportado para o Excel para atualizar os pontuação_GuessGame time_casa e time_visitante.
class PontuacaoTime(models.Model):
    campeonato = models.CharField(max_length=100)
    time = models.CharField(max_length=100)
    pontuacao_media_ponderada = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.time} - {self.campeonato}"
   
   
# IMPORTANTE:  Dar sequencia se necessário, verificar a utilidade da informação e reformular código para bucar os times na lista_próximos jogos
# Tabela atualizada automaticamente pela função calcular_probabilidade_vitoria no utils.py e de acordo com a class Pesos,
# utiliza-se o comands no terminal: python manage.py atuProbMarg Barcelona Valencia
class PontuTimeProbaMarg(models.Model):
    campeonato = models.CharField(max_length=100)
    time1 = models.CharField(max_length=100)
    time2 = models.CharField(max_length=100)
    probabilidade_vitoria_time1 = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    margem_vitoria_esperada_time1 = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    probabilidade_vitoria_time2 = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    margem_vitoria_esperada_time2 = models.DecimalField(max_digits=5, decimal_places=2, default=0)


# Tabela atualizada automaticamente pela função def Atualizar_SomaPontosTimeCampeonato() no utils.py e de acordo com a classe Aposta
# utiliza-se o comands no terminal: python manage.py atuPontosTimeCampeonato
class SomaPontosTimeCampeonato(models.Model):
    time = models.CharField(max_length=100)
    campeonato = models.CharField(max_length=100)
    soma_qtde_jogos =  models.IntegerField(default=0) # Campo novo
    soma_pontos = models.IntegerField(default=0)
    soma_vitorias = models.IntegerField(default=0)
    soma_empates = models.IntegerField(default=0)
    soma_derrotas = models.IntegerField(default=0)
    soma_gols_marcados = models.IntegerField(default=0)
    soma_gols_contra = models.IntegerField(default=0)
    soma_gols_saldo = models.IntegerField(default=0)
    soma_guessGameOdds_acertos = models.IntegerField(default=0)
    soma_casasApostasOdds_acertos = models.IntegerField(default=0)
    soma_zebra = models.IntegerField(default=0)
    soma_vitorias_casa = models.IntegerField(default=0)
    soma_vitorias_fora = models.IntegerField(default=0)
    soma_empates_casa = models.IntegerField(default=0)
    soma_empates_fora = models.IntegerField(default=0)
    soma_derrotas_casa = models.IntegerField(default=0) 
    soma_derrotas_fora = models.IntegerField(default=0)
    soma_favorito_empate = models.IntegerField(default=0)
    soma_favorito_derrota = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.time} - {self.campeonato}"
    


class Contato(models.Model):
    nome = models.CharField(max_length=50, blank=False)  # Campo obrigatório
    sobrenome = models.CharField(max_length=50, blank=False)  # Campo obrigatório
    email = models.EmailField(blank=False)  # Campo obrigatório
    telefone = PhoneNumberField(blank=False, null=False)  # Campo obrigatório
    assunto = models.CharField(max_length=200, blank=False)  # Campo obrigatório
    mensagem = models.TextField(blank=False)  # Campo obrigatório

    def __str__(self):
        return f'{self.nome} - {self.assunto}'




class VisitorLog(models.Model):
    ip = models.CharField(max_length=45)
    network = models.CharField(max_length=50, null=True)
    version = models.CharField(max_length=10)
    city = models.CharField(max_length=100, null=True)
    region = models.CharField(max_length=100, null=True)
    region_code = models.CharField(max_length=10, null=True)
    country = models.CharField(max_length=10)
    country_name = models.CharField(max_length=100)
    country_code = models.CharField(max_length=10)
    country_code_iso3 = models.CharField(max_length=10, null=True)
    country_capital = models.CharField(max_length=100, null=True)
    country_tld = models.CharField(max_length=10, null=True)
    continent_code = models.CharField(max_length=10, null=True)
    in_eu = models.BooleanField()
    postal = models.CharField(max_length=20, null=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    timezone = models.CharField(max_length=50)
    utc_offset = models.CharField(max_length=10)
    country_calling_code = models.CharField(max_length=10, null=True)
    currency = models.CharField(max_length=10)
    currency_name = models.CharField(max_length=50)
    languages = models.CharField(max_length=100, null=True)
    country_area = models.IntegerField()
    country_population = models.BigIntegerField()
    asn = models.CharField(max_length=50, null=True)
    org = models.CharField(max_length=100, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.ip} - {self.city}, {self.country_name}'


class CustomUser(AbstractUser):
    # Campos para consentimento de cookies
    cookies_accepted = models.BooleanField(default=False)  # Aceitação geral de cookies
    analytics_cookies = models.BooleanField(default=False)  # Aceitação de cookies analíticos
    marketing_cookies = models.BooleanField(default=False)   # Aceitação de cookies de marketing

    class Meta:
        db_table = 'customuser'  # Nome da tabela no banco de dados

    def __str__(self):
        return self.username



# Cadastro de usuários
class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    # Adicione outros campos de perfil se necessário
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=30, blank=True)
    birth_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.user.username


