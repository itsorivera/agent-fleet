# Guía de Arquitectura Cloud: Fundamentos de Landing Zones y Gobernanza Empresarial

Esta síntesis compila los conceptos, modelos operativos y patrones arquitectónicos clave analizados, diseñados para cerrar la brecha conceptual entre la **Arquitectura de Software/Soluciones** y la **Arquitectura de Plataforma Cloud**.

---

## 1. Definición Agnóstica y Propósito Esencial

Una **Landing Zone** no es una aplicación de software, un arquetipo de código ni un empaquetado de microservicios.

> **Definición Agnóstica:**  
> Es un entorno multi-cuenta/multi-suscripción aprovisionado mediante Infraestructura como Código (IaC), que establece la **identidad, conectividad de red, seguridad (guardrails), observabilidad y jerarquía organizativa** antes de que se despliegue cualquier carga de trabajo.

### La frontera de responsabilidades
* **Landing Zone (Cloud Platform / CCoE):** Provee el "terreno urbanizado" (red privada conectada, firewall perimetral, políticas de seguridad duras, centro de costos asignado).
* **Solución de Software (Arquitecto de Software):** Construye la "casa" dentro de ese terreno (microservicios en Kubernetes, bases de datos, colas de mensajería, lógica de negocio).

---

## 2. Los Dos Significados de "Landing Zone" (El Origen de la Confusión)

La industria (Azure CAF, AWS Prescriptive Guidance) usa el mismo término para dos alcances diferentes:

```mermaid
flowchart TD
  subgraph ALZ_GLOBAL ["1. Platform Landing Zone (Global / El Edificio)"]
      direction TB
      Root["Tenant Root (Entra ID / AWS Org)"]
      
      subgraph PLATFORM ["Suscripciones de Plataforma"]
          Net["Hub / Conectividad\n(Firewall, DNS, VPN)"]
          Sec["Gestión e Identidad\n(Logs, Key Vaults)"]
          Shared["Servicios Compartidos\n(APIM Central, Ingress)"]
      end
      
      subgraph VENDING ["Subscription Vending Machine (IaC Pipeline)"]
          Vendor["Aprovisionador de Nuevas Suscripciones"]
      end
  end

  subgraph WORKLOAD_MG ["2. Application Landing Zones (Las Oficinas)"]
      direction TB
      subgraph NONPROD_MG ["Management Group: Non-Prod"]
          SubDev["Suscripción: App-Dev\n(Políticas flexibles, bajo coste)"]
      end
      subgraph PROD_MG ["Management Group: Prod"]
          SubProd["Suscripción: App-Prod\n(Políticas duras, HA, Backups)"]
      end
  end

  Root --> PLATFORM
  Root --> WORKLOAD_MG
  Vendor -.->|Emite| SubDev
  Vendor -.->|Emite| SubProd
  Net <===>|VNet Peering Privado| SubDev
  Net <===>|VNet Peering Privado| SubProd
  Shared -.->|Expone APIs| SubDev
  Shared -.->|Expone APIs| SubProd

  classDef platform fill:#0d2f4f,stroke:#1a6fb0,stroke-width:2px,color:#fff;
  classDef workload fill:#1c3b2b,stroke:#2e8b57,stroke-width:2px,color:#fff;
  classDef root fill:#333,stroke:#666,stroke-width:2px,color:#fff;

  class Root root;
  class Net,Sec,Shared,Vendor platform;
  class SubDev,SubProd workload;
```

1. **Platform Landing Zone (Global):** Es única para toda la empresa. Contiene la infraestructura central compartida (red troncal, firewalls corporativos, APIM compartido y observabilidad central).
2. **Application Landing Zone (Workload):** Es la suscripción/cuenta individual que se le otorga a un equipo de desarrollo específico. Se genera mediante un pipeline automatizado (**Subscription Vending Machine**), integrándose a la red y a la gobernanza global sin recrear la infraestructura central.

---

## 3. Jerarquía y Mecanismos de Aislamiento

Para garantizar que un incidente en desarrollo o en un dominio de negocio no comprometa a toda la organización, los recursos se ordenan en cuatro niveles de contención:

```mermaid
graph TD
  A["<b>1. Management Groups (Carpetas)</b><br>Herencia de Azure Policies y Guardrails"] --> B["<b>2. Suscripciones / Cuentas</b><br>Límite de Blast Radius, Facturación, IAM e IPs"]
  B --> C["<b>3. Grupos de Recursos (RG)</b><br>Ciclo de vida común de componentes de software"]
  C --> D["<b>4. Recursos Individuales</b><br>Pods, BDs, Functions, Storage"]
```

| Nivel | Rol / Concepto | Función Arquitectónica |
| :--- | :--- | :--- |
| **Management Group** | Gobernanza jerárquica | Se definen políticas que aplican por herencia hacia abajo (ej. *“En Non-Prod se permiten VMs económicas; en Prod se exigen zonas de disponibilidad”*). |
| **Suscripción (o AWS Account)** | Frontera de aislamiento (*Blast Radius*) | Separa entornos (**Dev vs. Prod**) y dominios (**Pagos vs. Inventario**). Evita colisión de cuotas de cómputo y separa centros de costos. |
| **Grupo de Recursos (RG)** | Ciclo de vida de la aplicación | Agrupa recursos de una misma solución que nacen y mueren juntos (ej. `rg-pagos-backend-prod`). Borrar el RG no destruye la red ni la suscripción. |
| **Recurso** | Componente de cómputo/datos | El servicio individual desplegado (PostgreSQL, AKS, Azure Functions). |

---

## 4. Patrón de Integración en Malla: APIM Centralizado (Hub & Spoke)

Cuando la organización exige que todos los servicios pasen por un API Management centralizado:

```mermaid
sequenceDiagram
  autonumber
  actor Cliente as Usuario / Cliente Externo
  participant WAF as WAF / Ingress Perimetral
  participant APIM as APIM Central (Suscripción Platform Shared)
  participant SpokeProd as API Backend (Suscripción App-Prod)
  participant DB as BD Privada (Suscripción App-Prod)

  Cliente->>WAF: Solicitud HTTPS (api.empresa.com/v1/prestamos)
  WAF->>APIM: Inspección y validación de seguridad
  Note over APIM,SpokeProd: Tráfico viaja por Red Privada (VNet Peering / Private Link)
  APIM->>SpokeProd: Enrutamiento interno (IP Privada 10.240.x.x)
  SpokeProd->>DB: Consulta a BD interna (Sin IP Pública)
  DB-->>SpokeProd: Respuesta
  SpokeProd-->>APIM: Payload
  APIM-->>Cliente: Respuesta JSON consolidada
```

* **Suscripción de Plataforma:** El equipo de redes/plataforma mantiene la instancia de APIM y el WAF.
* **Suscripción del Dominio:** El equipo de software despliega sus APIs con **IPs privadas** en subredes aisladas.
* **Integración:** El equipo de software no administra el APIM; registra sus especificaciones (OpenAPI / Swagger) mediante Pull Requests a un pipeline federado de integración continua.

---

## 5. Greenfield vs. Brownfield: ¿Se puede implementar tarde?

* **Greenfield (Ideal / Deber Ser):** Se despliega la Landing Zone antes de que exista la primera aplicación en la nube. Ahorra refactorizaciones y colisiones de red posteriores.
* **Brownfield (Realidad de la Industria):** Se aplica sobre una nube que ya tiene aplicaciones en producción sin arquitectura formal:
1. Se construye la Landing Zone global en paralelo.
2. Se colocan las suscripciones existentes bajo un grupo transitorio (`Legacy` o `Migration`).
3. Se aplican políticas en modo **Auditoría (Audit-Only)** para detectar brechas sin romper producción.
4. Se corrigen las redes y se mueven las suscripciones al grupo definitivo (`Prod` o `Non-Prod`).

---

## 6. Equivalencias entre Proveedores Cloud

| Dimensión | Azure | AWS | Google Cloud (GCP) |
| :--- | :--- | :--- | :--- |
| **Framework Base** | Azure Landing Zones (CAF) | AWS Landing Zone / Well-Architected | Cloud Foundation Fabric |
| **Herramienta Orquestadora** | ALZ Terraform Module / Bicep | AWS Control Tower | Foundation Toolkit / Terraform |
| **Jerarquía de Políticas** | Management Groups + Azure Policy | AWS Organizations + SCPs | Organization Policies + Folders |
| **Límite de Aislamiento** | Subscription | AWS Account | GCP Project |
| **Dispensador de Entornos** | Subscription Vending Machine | Account Factory (AFT) | Project Factory Module |