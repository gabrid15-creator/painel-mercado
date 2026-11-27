//+------------------------------------------------------------------+
//| ReguaPainel: SÓ LEITURA. Não abre, altera nem fecha operação.    |
//| Manda os candles de 1 minuto do XAUUSD (fechados, últimas 1440   |
//| barras, em UTC) para ultimo.csv no repositório "painel-regua".   |
//| A chave fica só no computador: MQL5/Files/painel_token.txt       |
//| Criar a chave SÓ para o repositório painel-regua (Contents).     |
//| Instalar: copiar para MQL5/Experts, compilar no MetaEditor (F7), |
//| liberar https://api.github.com em Ferramentas > Opções > Expert  |
//| Advisors (WebRequest) e arrastar para um gráfico do XAUUSD.      |
//| Desfazer: tirar do gráfico, apagar o programa e o painel_token,  |
//| e revogar a chave no GitHub.                                     |
//+------------------------------------------------------------------+
#property copyright "Painel de mercado"
#property version   "1.00"
#property strict

input int    MinutosEntreEnvios = 15;
input string Repositorio        = "gabrid15-creator/painel-regua";
input string Ramo               = "main";

#define ARQ_CHAVE "painel_token.txt"
#define BARRAS    1440

string   chave = "";
datetime ultimaBarra = 0;     // última barra já enviada
datetime proximoEnvio = 0;    // relógio do computador (UTC)

void Aviso(const string t)
{
   string s = "ReguaPainel (só leitura)\n" + TimeToString(TimeLocal(), TIME_DATE|TIME_MINUTES) + "  " + t;
   Comment(s);
   Print("ReguaPainel: ", t);
}

int OnInit()
{
   if(StringFind(Repositorio, "painel-mercado") >= 0)   // a chave não pode alcançar o código do painel
   {
      Alert("ReguaPainel: use o repositório separado painel-regua.");
      return INIT_FAILED;
   }
   if(StringFind(_Symbol, "XAUUSD") != 0)
   {
      Alert("ReguaPainel: coloque no gráfico do XAUUSD.");
      return INIT_FAILED;
   }
   int h = FileOpen(ARQ_CHAVE, FILE_READ|FILE_TXT|FILE_ANSI);
   if(h == INVALID_HANDLE)
   {
      Alert("ReguaPainel: falta o arquivo MQL5/Files/", ARQ_CHAVE);
      return INIT_FAILED;
   }
   chave = FileReadString(h);
   FileClose(h);
   StringTrimLeft(chave);
   StringTrimRight(chave);
   if(StringLen(chave) < 20)
   {
      Alert("ReguaPainel: a chave em ", ARQ_CHAVE, " está vazia ou incompleta.");
      return INIT_FAILED;
   }
   EventSetTimer(30);
   Aviso("ligado, aguardando o primeiro envio");
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   EventKillTimer();
   Comment("");
}

void OnTimer()
{
   datetime agora = TimeGMT();
   if(agora < proximoEnvio) return;
   proximoEnvio = agora + 5 * 60;   // se falhar, tenta de novo em 5 minutos

   if(!TerminalInfoInteger(TERMINAL_CONNECTED)) { Aviso("sem conexão com a corretora"); return; }

   MqlRates r[];
   int n = CopyRates(_Symbol, PERIOD_M1, 1, BARRAS, r);   // posição 1: só barras fechadas
   if(n <= 0) { Aviso("sem barras ainda"); return; }
   if(r[n-1].time == ultimaBarra) { Aviso("mercado parado, nada novo"); return; }

   // diferença entre o horário do servidor da corretora e o UTC, em meias horas
   int desvio = (int)MathRound((double)(TimeTradeServer() - TimeGMT()) / 1800.0) * 1800;

   string csv = "# simbolo=" + _Symbol + " desvio_s=" + IntegerToString(desvio) +
                " gerado_utc=" + TimeToString(agora, TIME_DATE|TIME_MINUTES) + "\n" +
                "epoch_utc,abertura,maxima,minima,fechamento\n";
   for(int i = 0; i < n; i++)
      csv += IntegerToString((long)r[i].time - desvio) + "," +
             DoubleToString(r[i].open, _Digits) + "," + DoubleToString(r[i].high, _Digits) + "," +
             DoubleToString(r[i].low, _Digits) + "," + DoubleToString(r[i].close, _Digits) + "\n";

   if(Enviar(csv))
   {
      ultimaBarra = r[n-1].time;
      proximoEnvio = agora + MinutosEntreEnvios * 60;
      Aviso("enviado: " + IntegerToString(n) + " barras, último preço " + DoubleToString(r[n-1].close, _Digits));
   }
}

int Pedido(const string metodo, const string url, const string corpo, string &resposta)
{
   string cab = "Authorization: Bearer " + chave + "\r\n" +
                "Accept: application/vnd.github+json\r\n" +
                "User-Agent: ReguaPainel\r\n" +
                "Content-Type: application/json\r\n";
   char dados[], volta[];
   string cabVolta;
   if(StringLen(corpo) > 0) StringToCharArray(corpo, dados, 0, StringLen(corpo), CP_UTF8);
   ResetLastError();
   int cod = WebRequest(metodo, url, cab, 15000, dados, volta, cabVolta);
   if(cod == -1)
   {
      int erro = GetLastError();
      resposta = "";
      Aviso("falha de rede " + IntegerToString(erro) +
            " (conferir se https://api.github.com está liberado nas opções do MT5)");
      return -1;
   }
   resposta = CharArrayToString(volta, 0, WHOLE_ARRAY, CP_UTF8);
   return cod;
}

// valor do primeiro campo "sha" da resposta
string Sha(const string json)
{
   int p = StringFind(json, "\"sha\"");
   if(p < 0) return "";
   int a = StringFind(json, "\"", p + 5);
   if(a < 0) return "";
   int b = StringFind(json, "\"", a + 1);
   if(b < 0) return "";
   return StringSubstr(json, a + 1, b - a - 1);
}

string Base64(const string texto)
{
   uchar origem[], vazio[], saida[];
   StringToCharArray(texto, origem, 0, StringLen(texto), CP_UTF8);
   if(CryptEncode(CRYPT_BASE64, origem, vazio, saida) <= 0) return "";
   string s = CharArrayToString(saida);
   StringReplace(s, "\r", "");
   StringReplace(s, "\n", "");
   return s;
}

bool Enviar(const string csv)
{
   string url = "https://api.github.com/repos/" + Repositorio + "/contents/ultimo.csv";
   string resp;
   int cod = Pedido("GET", url + "?ref=" + Ramo, "", resp);
   if(cod == -1) return false;
   if(cod != 200 && cod != 404) { Aviso("o GitHub recusou a leitura, código " + IntegerToString(cod)); return false; }
   string sha = (cod == 200 ? Sha(resp) : "");

   string conteudo = Base64(csv);
   if(conteudo == "") { Aviso("falha ao preparar o arquivo"); return false; }
   string corpo = "{\"message\":\"regua\",\"branch\":\"" + Ramo + "\",";
   if(sha != "") corpo += "\"sha\":\"" + sha + "\",";
   corpo += "\"content\":\"" + conteudo + "\"}";

   cod = Pedido("PUT", url, corpo, resp);
   if(cod == -1) return false;
   if(cod != 200 && cod != 201) { Aviso("o GitHub recusou o envio, código " + IntegerToString(cod)); return false; }
   return true;
}
