WITH pd AS (
    SELECT DISTINCT
        -- Identificadores
        a.key_value,
        a.cod_cli,
        date_format(
            date_parse(CAST(a.cod_mes AS varchar), '%Y%m') - interval '1' month,
            '%Y%m'
        ) AS codmes_lag1,
        CAST(a.cod_mes AS INTEGER) AS cod_mes

        -- Fechas

    FROM d_perm_aws.t_agg_alertas_plaft a
        WHERE a.cod_mes BETWEEN '202507' AND '202604'
            AND a.desc_subsegmento = 'Renta Alta'
),

target AS (
    SELECT 
        codunico,
        periodo_alerta,
        tipo_alerta_n2,
        trx_riesgo_cliente,
        MAX(calificacion_monitoreo) AS flg_alerta
    FROM e_perm_aws.t_alertas_plaft
    GROUP BY codunico, periodo_alerta, tipo_alerta_n2,trx_riesgo_cliente
),
base AS(
SELECT 
    a.*,
    b.tipo_alerta_n2,
    b.trx_riesgo_cliente, 
    CASE 
        WHEN b.flg_alerta = '1' THEN 1 
        ELSE 0 
    END AS target_m
FROM pd a
INNER JOIN target b
    ON a.cod_cli = b.codunico
    AND cast(a.cod_mes as varchar) = b.periodo_alerta
    where tipo_alerta_n2='AUTOMATICA'
    )

select 
cod_mes,
count(distinct cod_cli) as cantidad,
sum(target_m) as target 
from base 

group by 1 