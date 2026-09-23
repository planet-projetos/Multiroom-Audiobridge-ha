# Multiroom AudioBridge for Home Assistant

Integração não oficial para controlar matrizes AudioBRIDGE em Home Assistant via Telnet.

## Funcionalidades

- Controle de potência por zona
- Controle de volume e mute
- Seleção de entrada por zona
- Suporte ao fluxo de configuração do Home Assistant
- Compatível com integrações HACS

## Instalação

1. Clone este repositório ou adicione-o como repositório customizado no HACS.
2. Instale o repositório como custom integration.
3. Reinicie o Home Assistant.
4. Adicione a integração via Configurações > Dispositivos e serviços > Integrações.

## Configuração

Informe o endereço IP/hostname e a porta do controlador AudioBRIDGE.
Informe na próxima pagina os nomes de zonas e entradas. 
Informe na próxima pagina os nomes e entidades de cada zona
Para alterar algum basta usar a opção configurar na pagina da integração

## Observações

- A integração usa comunicação local via Telnet.
- A porta padrão é 23.

## Licença

Este projeto é fornecido sem garantia e é destinado a uso pessoal e de laboratório.
