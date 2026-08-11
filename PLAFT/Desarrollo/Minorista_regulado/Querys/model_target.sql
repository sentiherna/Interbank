-- Colocar query para armar el target con la poblacion del modelo
WITH pd AS (
    SELECT DISTINCT
        -- Identificadores
        a.key_value,
        a.cod_cli,
        date_format(
            date_parse(CAST(a.cod_mes AS varchar), '%Y%m') - interval '1' month,
            '%Y%m'
        ) AS codmes_lag1,
        CAST(a.cod_mes AS INTEGER) AS cod_mes,

        -- Fechas

    FROM d_perm_aws.t_agg_alertas_plaft a
        WHERE a.cod_mes BETWEEN '202501' AND '202604'
            AND a.desc_subsegmento = 'BPE'
),

target AS (
    SELECT 
        codunico,
        periodo_alerta,
        tipo_alerta_n2 as tip_alerta,
        trx_riesgo_cliente,
        MAX(calificacion_monitoreo) AS flg_alerta
    FROM e_perm_aws.t_alertas_plaft
    GROUP BY codunico, periodo_alerta, tipo_alerta_n2,trx_riesgo_cliente
)

SELECT 
    a.*,
    b.tip_alerta,
    b.trx_riesgo_cliente, 
    CASE 
        WHEN b.flg_alerta = '1' THEN 1 
        ELSE 0 
    END AS target_m
FROM pd a
LEFT JOIN target b
    ON a.cod_cli = b.codunico
    AND cast(a.cod_mes as varchar) = b.periodo_alerta
--   AND codmes_lag1 = c.periodo_alerta
