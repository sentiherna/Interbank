CREATE TABLE "disc_comercial"."plaft_pn_masivo_inferencia_0726" WITH (
     format = 'parquet',
  external_location = 's3://ibk-discovery-comercial-us-east-1-654654352211-data/discovery/comercial/sanherna/PLAFT/PN/MASIVO/DATA_INFERENCIA_PILOTO/INFERENCIA/',
  partitioned_by = ARRAY [ 'periodo' ]
) AS



WITH alarmas_positivos AS (
    SELECT
        LPAD(CAST(a.cod_cli AS VARCHAR), 10, '0')                            AS cuc_num,
        CASE WHEN a.desc_subsegmento IN ('Masivo', 'Masivo Dependiente', 'Masivo Independiente')
             THEN 'Masivo' ELSE a.desc_subsegmento END                      AS subsegmento,
        a.cod_mes,
        CAST(DATE_PARSE(a.cod_mes, '%Y%m') AS DATE)                        AS mes,
         cast(a.flg_alerta  as int)                                                      AS target,
        'con_riesgo'                                                        AS tipo_origen,
        a.key_value,
        -- Atributos de cliente
        a.num_antiguedad,
        a.flg_activo,
        a.flg_inteligo,
        -- Features PLAFT (ya en lag-1 en t_agg_alertas_plaft)
        a.cnt_dif_abn_crgsefe_6m,
        a.flg_vrcn_abonos_5m_1m,
        a.imp_trx_abonostot_1m,                                            -- intermedio para fe_zscore_abonos
        a.imp_trx_abonosefect_3m,
        a.imp_trx_abonostot_3m,
        a.imp_trx_abonostot_6m,                                            -- intermedio para fe_zscore_abonos
        a.imp_trx_abonosefect_12m,
        a.max_trx_abonos_1m,
        a.imp_trx_abonostot_9m,
        a.imp_trx_cargosefe_3m,
        a.imp_trx_cargostot_1m,
        a.imp_trx_cargostot_3m,
        a.imp_trx_cargostot_6m,                                            -- intermedio para fe_zscore_cargos
        a.imp_trx_cargosefe_12m,
        a.max_trx_cargos_12m,
        a.cnt_trx_abonosefect_12m,
        a.cnt_trx_abonostot_12m,
        a.cnt_trx_cargostot_12m,
        a.cnt_meses_siningresos_12m,
        a.cnt_meses_sinegresos_12m,
        TRY_CAST(a.mto_pas_soles AS DOUBLE)                                AS mto_pas_soles,
        -- ROS (señal directa de actividad sospechosa)
        TRY_CAST(a.cnt_ros_hist AS DOUBLE)                                 AS cnt_ros_hist,
        a.flg_ros_12m,
        -- Estructuración (operaciones por debajo del umbral de reporte)
        TRY_CAST(a.mto_ro_debajo_umbral AS DOUBLE)                         AS mto_ro_debajo_umbral,
        a.cnt_ro_debajo_umbral,
        TRY_CAST(a.imp_trx_debajo10k_ing_12m AS DOUBLE)                   AS imp_trx_debajo10k_ing_12m,
        a.cnt_trx_debajo10k_ing_12m,
        TRY_CAST(a.imp_trx_debajo10k_egr_12m AS DOUBLE)                   AS imp_trx_debajo10k_egr_12m,
        a.cnt_trx_debajo10k_egr_12m,
        -- Exterior (movimiento de fondos al/desde el exterior)
        a.flg_al_ext_12m,
        a.flg_del_ext_12m,
        TRY_CAST(a.mto_al_ext_12m AS DOUBLE)                              AS mto_al_ext_12m,
        TRY_CAST(a.mto_del_ext_12m AS DOUBLE)                             AS mto_del_ext_12m,
        TRY_CAST(a.mto_ing_delextrsgalto_12m AS DOUBLE)                   AS mto_ing_delextrsgalto_12m,
        TRY_CAST(a.mto_al_extrsgaltot_12m AS DOUBLE)                      AS mto_al_extrsgaltot_12m,
        TRY_CAST(a.rat_ing_dl_xt_lt_tot_12m AS DOUBLE)                    AS rat_ing_dl_xt_lt_tot_12m,
        TRY_CAST(a.rat_mto_al_xt_lt_12m AS DOUBLE)                        AS rat_mto_al_xt_lt_12m,
        -- PEP y listas de riesgo
        a.flg_pep,
        a.cod_rsg_pep,
        a.cod_v01_lista_rsg,
        TRY_CAST(a.mto_cp_pep_ing AS DOUBLE)                              AS mto_cp_pep_ing,
        TRY_CAST(a.mto_cp_pep_egr AS DOUBLE)                              AS mto_cp_pep_egr,
        -- Contraparte con riesgo
        a.flg_t1cp_rosing_12m,
        a.flg_cp_ros_egr_12m,
        TRY_CAST(a.mto_cp_tot_ing_ros AS DOUBLE)                          AS mto_cp_tot_ing_ros,
        TRY_CAST(a.mto_cp_tot_egr_ros AS DOUBLE)                          AS mto_cp_tot_egr_ros,
        -- Riesgo geográfico y de canal
        a.cod_v12_lugar_rsdn_rsg,
        a.cod_v13_lugar_op_rsg_12m,
        a.cod_v11_pais_op_rsg,
        a.cod_v16_canal_op_rsg_12m,
        -- Tiendas y canales de alto riesgo
        TRY_CAST(a.mto_ing_tnda_rsg_alto_12m AS DOUBLE)                   AS mto_ing_tnda_rsg_alto_12m,
        a.cnt_tienda_rsg_alto_12m,
        TRY_CAST(a.mto_ing_cnl_rsg_alto_12m AS DOUBLE)                    AS mto_ing_cnl_rsg_alto_12m,
        a.cnt_canal_rsg_alto_12m,
        -- Historial de alertas y variación de efectivo adicionales
        a.flg_alerta_12m,
        a.cnt_alerta_hist,
        a.flg_vrcn_efe_cargos_5m_1m,
        TRY_CAST(a.mto_dif_abn_crgsefe_6m AS DOUBLE)                      AS mto_dif_abn_crgsefe_6m,
        TRY_CAST(a.rat_trx_mntabnsefetot_6m AS DOUBLE)                    AS rat_trx_mntabnsefetot_6m,
        TRY_CAST(a.rat_mntcrgsefetot_6m AS DOUBLE)                        AS rat_mntcrgsefetot_6m
    FROM e_perm_aws.t_agg_alertas_plaft a
    WHERE a.p_codmes BETWEEN '202607' AND '202607'
      AND a.desc_subsegmento IN ('Masivo', 'Masivo Dependiente', 'Masivo Independiente')
      AND a.flg_alerta in ('0','1')
),

clientes_con_actividad AS (
    SELECT
        LPAD(CAST(cuc_num AS VARCHAR), 10, '0') AS cuc_num,
        DATE_FORMAT(DATE_TRUNC('month', fechinievento), '%Y%m') AS mes_trx
    FROM e_perm_aws.t_fct_transacciones_captaciones
    WHERE tipopersona = 'N'
      AND fechinievento IS NOT NULL
      AND p_mesinformacion BETWEEN
            DATE_FORMAT(DATE_ADD('month', -1, DATE_PARSE('202607', '%Y%m')), '%Y%m')
        AND DATE_FORMAT(DATE_ADD('month', -1, DATE_PARSE('202607', '%Y%m')), '%Y%m')
      AND DATE_TRUNC('month', fechinievento)
            BETWEEN DATE_ADD('month', -1, DATE_PARSE('202607', '%Y%m'))
                AND DATE_ADD('day', -1, DATE_PARSE('202607', '%Y%m'))
    GROUP BY LPAD(CAST(cuc_num AS VARCHAR), 10, '0'), DATE_FORMAT(DATE_TRUNC('month', fechinievento), '%Y%m')
   -- HAVING SUM(montotransaccion) >= 0
),

alarmas_nunca_alertado AS (
    -- Sample de 10k registros por mes (rand()), sobre clientes con actividad > 5k en el mes previo.
    SELECT
        cuc_num, subsegmento, cod_mes, mes, target, tipo_origen, key_value,
        num_antiguedad, flg_activo, flg_inteligo,
        cnt_dif_abn_crgsefe_6m, flg_vrcn_abonos_5m_1m, imp_trx_abonostot_1m,
        imp_trx_abonosefect_3m, imp_trx_abonostot_3m, imp_trx_abonostot_6m,
        imp_trx_abonosefect_12m, max_trx_abonos_1m, imp_trx_abonostot_9m,
        imp_trx_cargosefe_3m, imp_trx_cargostot_1m, imp_trx_cargostot_3m,
        imp_trx_cargostot_6m, imp_trx_cargosefe_12m, max_trx_cargos_12m,
        cnt_trx_abonosefect_12m, cnt_trx_abonostot_12m, cnt_trx_cargostot_12m,
        cnt_meses_siningresos_12m, cnt_meses_sinegresos_12m, mto_pas_soles,
        cnt_ros_hist, flg_ros_12m,
        mto_ro_debajo_umbral, cnt_ro_debajo_umbral,
        imp_trx_debajo10k_ing_12m, cnt_trx_debajo10k_ing_12m,
        imp_trx_debajo10k_egr_12m, cnt_trx_debajo10k_egr_12m,
        flg_al_ext_12m, flg_del_ext_12m,
        mto_al_ext_12m, mto_del_ext_12m, mto_ing_delextrsgalto_12m, mto_al_extrsgaltot_12m,
        rat_ing_dl_xt_lt_tot_12m, rat_mto_al_xt_lt_12m,
        flg_pep, cod_rsg_pep, cod_v01_lista_rsg, mto_cp_pep_ing, mto_cp_pep_egr,
        flg_t1cp_rosing_12m, flg_cp_ros_egr_12m, mto_cp_tot_ing_ros, mto_cp_tot_egr_ros,
        cod_v12_lugar_rsdn_rsg, cod_v13_lugar_op_rsg_12m, cod_v11_pais_op_rsg, cod_v16_canal_op_rsg_12m,
        mto_ing_tnda_rsg_alto_12m, cnt_tienda_rsg_alto_12m, mto_ing_cnl_rsg_alto_12m, cnt_canal_rsg_alto_12m,
        flg_alerta_12m, cnt_alerta_hist, flg_vrcn_efe_cargos_5m_1m,
        mto_dif_abn_crgsefe_6m, rat_trx_mntabnsefetot_6m, rat_mntcrgsefetot_6m
    FROM (
        SELECT
            LPAD(CAST(a.cod_cli AS VARCHAR), 10, '0')                        AS cuc_num,
            CASE WHEN a.desc_subsegmento IN ('Masivo', 'Masivo Dependiente', 'Masivo Independiente')
                 THEN 'Masivo' ELSE a.desc_subsegmento END                  AS subsegmento,
            a.cod_mes,
            CAST(DATE_PARSE(a.cod_mes, '%Y%m') AS DATE)                    AS mes,
            0                                                               AS target,
            'nunca_alertado'                                                AS tipo_origen,
            a.key_value,
            a.num_antiguedad,
            a.flg_activo,
            a.flg_inteligo,
            a.cnt_dif_abn_crgsefe_6m,
            a.flg_vrcn_abonos_5m_1m,
            a.imp_trx_abonostot_1m,
            a.imp_trx_abonosefect_3m,
            a.imp_trx_abonostot_3m,
            a.imp_trx_abonostot_6m,
            a.imp_trx_abonosefect_12m,
            a.max_trx_abonos_1m,
            a.imp_trx_abonostot_9m,
            a.imp_trx_cargosefe_3m,
            a.imp_trx_cargostot_1m,
            a.imp_trx_cargostot_3m,
            a.imp_trx_cargostot_6m,
            a.imp_trx_cargosefe_12m,
            a.max_trx_cargos_12m,
            a.cnt_trx_abonosefect_12m,
            a.cnt_trx_abonostot_12m,
            a.cnt_trx_cargostot_12m,
            a.cnt_meses_siningresos_12m,
            a.cnt_meses_sinegresos_12m,
            TRY_CAST(a.mto_pas_soles AS DOUBLE)                            AS mto_pas_soles,
            TRY_CAST(a.cnt_ros_hist AS DOUBLE)                             AS cnt_ros_hist,
            a.flg_ros_12m,
            TRY_CAST(a.mto_ro_debajo_umbral AS DOUBLE)                     AS mto_ro_debajo_umbral,
            a.cnt_ro_debajo_umbral,
            TRY_CAST(a.imp_trx_debajo10k_ing_12m AS DOUBLE)               AS imp_trx_debajo10k_ing_12m,
            a.cnt_trx_debajo10k_ing_12m,
            TRY_CAST(a.imp_trx_debajo10k_egr_12m AS DOUBLE)               AS imp_trx_debajo10k_egr_12m,
            a.cnt_trx_debajo10k_egr_12m,
            a.flg_al_ext_12m,
            a.flg_del_ext_12m,
            TRY_CAST(a.mto_al_ext_12m AS DOUBLE)                          AS mto_al_ext_12m,
            TRY_CAST(a.mto_del_ext_12m AS DOUBLE)                         AS mto_del_ext_12m,
            TRY_CAST(a.mto_ing_delextrsgalto_12m AS DOUBLE)               AS mto_ing_delextrsgalto_12m,
            TRY_CAST(a.mto_al_extrsgaltot_12m AS DOUBLE)                  AS mto_al_extrsgaltot_12m,
            TRY_CAST(a.rat_ing_dl_xt_lt_tot_12m AS DOUBLE)                AS rat_ing_dl_xt_lt_tot_12m,
            TRY_CAST(a.rat_mto_al_xt_lt_12m AS DOUBLE)                    AS rat_mto_al_xt_lt_12m,
            a.flg_pep,
            a.cod_rsg_pep,
            a.cod_v01_lista_rsg,
            TRY_CAST(a.mto_cp_pep_ing AS DOUBLE)                          AS mto_cp_pep_ing,
            TRY_CAST(a.mto_cp_pep_egr AS DOUBLE)                          AS mto_cp_pep_egr,
            a.flg_t1cp_rosing_12m,
            a.flg_cp_ros_egr_12m,
            TRY_CAST(a.mto_cp_tot_ing_ros AS DOUBLE)                      AS mto_cp_tot_ing_ros,
            TRY_CAST(a.mto_cp_tot_egr_ros AS DOUBLE)                      AS mto_cp_tot_egr_ros,
            a.cod_v12_lugar_rsdn_rsg,
            a.cod_v13_lugar_op_rsg_12m,
            a.cod_v11_pais_op_rsg,
            a.cod_v16_canal_op_rsg_12m,
            TRY_CAST(a.mto_ing_tnda_rsg_alto_12m AS DOUBLE)               AS mto_ing_tnda_rsg_alto_12m,
            a.cnt_tienda_rsg_alto_12m,
            TRY_CAST(a.mto_ing_cnl_rsg_alto_12m AS DOUBLE)                AS mto_ing_cnl_rsg_alto_12m,
            a.cnt_canal_rsg_alto_12m,
            a.flg_alerta_12m,
            a.cnt_alerta_hist,
            a.flg_vrcn_efe_cargos_5m_1m,
            TRY_CAST(a.mto_dif_abn_crgsefe_6m AS DOUBLE)                  AS mto_dif_abn_crgsefe_6m,
            TRY_CAST(a.rat_trx_mntabnsefetot_6m AS DOUBLE)                AS rat_trx_mntabnsefetot_6m,
            TRY_CAST(a.rat_mntcrgsefetot_6m AS DOUBLE)                    AS rat_mntcrgsefetot_6m,
            ROW_NUMBER() OVER (PARTITION BY a.cod_mes ORDER BY rand())     AS rn
        FROM e_perm_aws.t_agg_alertas_plaft a
        LEFT JOIN clientes_con_actividad ca
            ON  LPAD(CAST(a.cod_cli AS VARCHAR), 10, '0') = ca.cuc_num
            AND DATE_FORMAT(DATE_ADD('month', -1, DATE_PARSE(a.cod_mes, '%Y%m')), '%Y%m') = ca.mes_trx
        WHERE a.p_codmes BETWEEN '202607' AND '202607'
          AND a.desc_subsegmento IN ('Masivo', 'Masivo Dependiente', 'Masivo Independiente')
          AND a.flg_alerta IS NULL
    ) ranked
),

alarmas AS (
    SELECT * FROM alarmas_positivos
    UNION ALL
    SELECT * FROM alarmas_nunca_alertado
),

-- Lista única de cuc_num — materializada una vez para INNER JOINs eficientes
-- en las CTEs de tablas e_perm_aws.* (evita IN (SELECT DISTINCT ...)).
alarmas_ids AS (
    SELECT DISTINCT cuc_num
    FROM alarmas
),

base_credito AS (
    SELECT
        bi.cuc_num,
        DATE_TRUNC('month', DATE(tc.transaccion_fc))                       AS mes,
        tc.transaccion_pen_amt,
        tc.autorizacion_ind
    FROM e_perm_aws.T_FCT_TRANSACCION_TARJ_CREDITO tc
    INNER JOIN alarmas_ids bi
        ON LPAD(CAST(tc.cuc_num AS VARCHAR), 10, '0') = bi.cuc_num
    WHERE tc.trx_limpia_ind = 1
      -- Partition prune por p_proceso_fc (YYYYMMDD), rango lag-1 de [codmes_ini, codmes_fin].
      AND tc.p_proceso_fc BETWEEN
            DATE_FORMAT(DATE_ADD('month', -1, DATE_PARSE('202607', '%Y%m')), '%Y%m%d')
        AND DATE_FORMAT(DATE_ADD('day', -1, DATE_PARSE('202607', '%Y%m')), '%Y%m%d')
      AND DATE_TRUNC('month', DATE(tc.transaccion_fc))
            BETWEEN DATE_ADD('month', -1, DATE_PARSE('202607', '%Y%m'))
                AND DATE_ADD('day', -1, DATE_PARSE('202607', '%Y%m'))
),

features_credito AS (
    SELECT
        cuc_num,
        mes,
        SUM(transaccion_pen_amt)                                           AS tc_total_monto_mes,
        STDDEV(transaccion_pen_amt)                                        AS tc_std_monto_mes,
        SUM(CASE WHEN autorizacion_ind = 'N' THEN 1 ELSE 0 END)
            / NULLIF(CAST(COUNT(*) AS DOUBLE), 0)                         AS tc_pct_no_autorizadas
    FROM base_credito
    GROUP BY cuc_num, mes
),

base_debito AS (
    SELECT
        bi.cuc_num,
        DATE(td.transaccion_fc)                                            AS fecha_trx,
        DATE_TRUNC('month', DATE(td.transaccion_fc))                       AS mes,
        td.transaccion_pen_amt,
        td.transaccion_hr
    FROM e_perm_aws.T_FCT_TRX_TARJ_DEBITO td
    INNER JOIN alarmas_ids bi
        ON LPAD(CAST(td.cuc_num AS VARCHAR), 10, '0') = bi.cuc_num
    WHERE td.trx_limpia_ind = 1
      -- Partition prune por p_proceso_fc (YYYYMMDD), rango lag-1 de [codmes_ini, codmes_fin].
      AND td.p_proceso_fc BETWEEN
            DATE_FORMAT(DATE_ADD('month', -1, DATE_PARSE('202607', '%Y%m')), '%Y%m%d')
        AND DATE_FORMAT(DATE_ADD('day', -1, DATE_PARSE('202607', '%Y%m')), '%Y%m%d')
      AND DATE_TRUNC('month', DATE(td.transaccion_fc))
            BETWEEN DATE_ADD('month', -1, DATE_PARSE('202607', '%Y%m'))
                AND DATE_ADD('day', -1, DATE_PARSE('202607', '%Y%m'))
),

base_debito_ts AS (
    SELECT *,
        CAST(
            DATE_PARSE(
                CAST(fecha_trx AS VARCHAR) || ' ' || transaccion_hr,
                '%Y-%m-%d %H:%i:%s.%f'
            ) AS TIMESTAMP
        ) AS ts_trx
    FROM base_debito
),

debito_burst AS (
    SELECT
        cuc_num,
        mes,
        ts_trx,
        transaccion_pen_amt,
        SUM(transaccion_pen_amt) OVER (
            PARTITION BY cuc_num ORDER BY ts_trx
            RANGE BETWEEN INTERVAL '1' HOUR PRECEDING AND CURRENT ROW
        ) AS monto_burst_1h,
        DATE_DIFF('minute',
            LAG(ts_trx) OVER (PARTITION BY cuc_num ORDER BY ts_trx),
            ts_trx
        ) AS minutos_entre_trx
    FROM base_debito_ts
),

features_debito AS (
    SELECT
        cuc_num,
        mes,
        AVG(monto_burst_1h)                                                AS td_avg_monto_1h,
        SUM(transaccion_pen_amt)                                           AS td_monto_total,
        AVG(minutos_entre_trx)                                             AS td_gap_promedio
    FROM debito_burst
    GROUP BY cuc_num, mes
),

trx_agregadas AS (
    SELECT
        cap.cuc_num,
        cap.mes,
        CAST(MAX(cap.daily_count) AS DOUBLE) / NULLIF(COUNT(*), 0)         AS concentracion_dia_max,
        SUM(CASE WHEN cap.acf_debito_o_credito = '1' AND cap.monedacd = 'PSS'
                 THEN cap.montotransaccion ELSE 0 END)                      AS monto_creditos_soles,
        SUM(CASE WHEN cap.acf_debito_o_credito = '2' AND cap.monedacd = 'PSS'
                 THEN cap.montotransaccion ELSE 0 END)                      AS monto_debitos_soles,
        SUM(CASE WHEN cap.tipo_trx = 'EFECTIVO' AND cap.monedacd = 'PSS'
                 THEN cap.montotransaccion ELSE 0 END)                      AS monto_efectivo_soles,
        MAX(CASE WHEN cap.tipo_trx NOT IN ('ITF_IMPUESTO', 'INTERESES') AND cap.monedacd = 'PSS'
                 THEN cap.montotransaccion END)                             AS monto_max_soles,
        AVG(CASE WHEN cap.tipo_trx NOT IN ('ITF_IMPUESTO', 'INTERESES') AND cap.monedacd = 'USD'
                 THEN cap.montotransaccion END)                             AS monto_promedio_dolares,
        STDDEV(CASE WHEN cap.tipo_trx NOT IN ('ITF_IMPUESTO', 'INTERESES') AND cap.monedacd = 'PSS'
                    THEN cap.montotransaccion END)                          AS monto_std_soles,
        SUM(CASE WHEN cap.tipo_trx NOT IN ('ITF_IMPUESTO', 'INTERESES') AND cap.monedacd = 'USD'
                 THEN cap.montotransaccion ELSE 0 END)                      AS monto_total_dolares,
        SUM(CASE WHEN cap.tipo_trx NOT IN ('ITF_IMPUESTO', 'INTERESES') AND cap.monedacd = 'PSS'
                 THEN cap.montotransaccion ELSE 0 END)                      AS monto_total_soles,
        SUM(CASE WHEN cap.tipo_trx = 'TRANSFERENCIA' AND cap.monedacd = 'PSS'
                 THEN cap.montotransaccion ELSE 0 END)                      AS monto_transferencias_soles,
        COUNT(DISTINCT cap.codinstcanal)                                    AS n_canales_distintos,
        COUNT(CASE WHEN cap.tipo_trx = 'CONSUMO_POS' THEN 1 END)           AS n_consumos,
        COUNT(DISTINCT cap.cuentacd)                                        AS n_cuentas_distintas,
        COUNT(CASE WHEN cap.tipo_trx NOT IN ('ITF_IMPUESTO', 'INTERESES')
                       AND cap.codinstcanal = 'APP' THEN 1 END)             AS n_trx_app,
        COUNT(CASE WHEN cap.tipo_trx = 'EFECTIVO' THEN 1 END)              AS n_trx_efectivo,
        COUNT(CASE WHEN cap.tipo_trx NOT IN ('ITF_IMPUESTO', 'INTERESES')
                       AND HOUR(CAST(cap.horainievento AS TIME)) BETWEEN 0 AND 5
                   THEN 1 END)                                              AS n_trx_madrugada,
        COUNT(CASE WHEN cap.tipo_trx NOT IN ('ITF_IMPUESTO', 'INTERESES') THEN 1 END)
                                                                            AS n_trx_mes,
        COUNT(CASE WHEN cap.tipo_trx NOT IN ('ITF_IMPUESTO', 'INTERESES')
                       AND cap.flg_mismocliente = '1' THEN 1 END)          AS n_trx_mismo_cliente,
        COUNT(CASE WHEN cap.tipo_trx NOT IN ('ITF_IMPUESTO', 'INTERESES')
                       AND HOUR(CAST(cap.horainievento AS TIME)) BETWEEN 18 AND 23
                   THEN 1 END)                                              AS n_trx_noche,
        COUNT(CASE WHEN cap.tipo_trx = 'OTROS' THEN 1 END)                 AS n_trx_otros,
        COUNT(CASE WHEN cap.tipo_trx NOT IN ('ITF_IMPUESTO', 'INTERESES')
                       AND cap.tipo_trx = 'PAGOS' THEN 1 END)              AS n_trx_pagos,
        CAST(COUNT(CASE WHEN cap.acf_debito_o_credito = '2' THEN 1 END) AS DOUBLE)
            / NULLIF(COUNT(CASE WHEN cap.acf_debito_o_credito = '1' THEN 1 END), 0)
                                                                            AS ratio_debito_credito
    FROM (
        SELECT
            inner_q.*,
            COUNT(*) OVER (
                PARTITION BY inner_q.cuc_num, DATE(inner_q.fechinievento)
            ) AS daily_count
        FROM (
            SELECT
                bi.cuc_num,
                DATE_TRUNC('month', t.fechinievento)                       AS mes,
                t.fechinievento,
                t.montotransaccion,
                t.monedacd,
                t.acf_debito_o_credito,
                t.codinstcanal,
                t.cuentacd,
                t.flg_mismocliente,
                t.horainievento,
                CASE
                    WHEN t.descevento IN ('RET CAJERO', 'RET AGENTE', 'DEP EFE  ATM', 'RETIRO EFECTIVO', 'DEPOSITO VENTAN', 'DEPOSITO DIR')
                        THEN 'EFECTIVO'
                    WHEN t.descevento IN ('TRANSF ALCAN', 'RETIRO ALCAN', 'ABONO ALCANC')
                        THEN 'ALCANCIA'
                    WHEN t.descevento IN ('TRANSFER BPI', 'I-BANC', 'TRAN TIL', 'Transf Plin', 'CARGO TRANSFERENCIA')
                        OR t.descevento LIKE 'YAPE%'
                        OR t.descevento LIKE 'Yape%'
                        OR t.descevento LIKE 'Plin-%'
                        OR t.descevento LIKE 'Plin %'
                        OR t.descevento = 'YAPE'
                        THEN 'TRANSFERENCIA'
                    WHEN t.descevento IN ('PAGO MI TC', 'PPA PAGOS', 'PPA PRVIZI', 'PAGO.REMESA', 'N/D REC.CELULAR')
                        THEN 'PAGOS'
                    WHEN t.descevento LIKE 'ITF %' OR t.descevento LIKE 'ITF_%'
                        THEN 'ITF_IMPUESTO'
                    WHEN t.descevento = 'INTERESES GANADO'
                        THEN 'INTERESES'
                    WHEN t.descevento IN ('REMUNE.BCP', 'MANTENIMIENTO')
                        THEN 'BANCARIO_INTERNO'
                    WHEN t.descevento IN ('Tambo', 'Plaza Vea', 'Tottus', 'Mifarma', 'Metro', 'Vendomatica', 'Indrive')
                        OR t.descevento LIKE 'Google%'
                        OR t.descevento LIKE 'PYU*%'
                        OR t.descevento LIKE 'Apple%'
                        OR t.descevento LIKE 'Rappi%'
                        THEN 'CONSUMO_POS'
                    ELSE 'OTROS'
                END AS tipo_trx
            FROM e_perm_aws.t_fct_transacciones_captaciones t
            INNER JOIN alarmas_ids bi
                ON LPAD(CAST(t.cuc_num AS VARCHAR), 10, '0') = bi.cuc_num
            WHERE t.tipopersona = 'N'
              AND t.fechinievento IS NOT NULL
              -- Partition prune por p_mesinformacion (rango lag-1 de [codmes_ini, codmes_fin]).
              AND t.p_mesinformacion BETWEEN
                    DATE_FORMAT(DATE_ADD('month', -1, DATE_PARSE('202508', '%Y%m')), '%Y%m')
                AND DATE_FORMAT(DATE_ADD('month', -1, DATE_PARSE('202604', '%Y%m')), '%Y%m')
        ) inner_q
    ) cap
    GROUP BY 1, 2
),

v360_reducido AS (
    SELECT
        v.cuc,
        v.codmes,
        v.saldo_prom_tot_pasivo
    FROM e_perm_aws.V_AWS_360_CLIENTE_MES v
    INNER JOIN alarmas_ids bi
        ON LPAD(CAST(v.cuc AS VARCHAR), 10, '0') = bi.cuc_num
    -- Partition prune: rango lag-1 de [codmes_ini, codmes_fin].
    WHERE v.p_codmes BETWEEN
            DATE_FORMAT(DATE_ADD('month', -1, DATE_PARSE('202607', '%Y%m')), '%Y%m')
        AND DATE_FORMAT(DATE_ADD('month', -1, DATE_PARSE('202607', '%Y%m')), '%Y%m')
)

SELECT
    -- Operativas
    a.cuc_num,
    a.cod_mes,
    a.mes,
    a.subsegmento,
    a.target,
    a.tipo_origen,
    a.key_value,
    -- Atributos de cliente
    a.num_antiguedad,
    a.flg_activo,
    a.flg_inteligo,
    -- Features PLAFT (t_agg_alertas_plaft, ya en lag-1)
    a.cnt_dif_abn_crgsefe_6m,
    a.flg_vrcn_abonos_5m_1m,
    a.imp_trx_abonosefect_3m,
    a.imp_trx_cargosefe_12m,
    a.max_trx_cargos_12m,
    a.imp_trx_cargostot_1m,
    a.imp_trx_cargosefe_3m,
    a.imp_trx_cargostot_3m,
    a.cnt_trx_abonosefect_12m,
    a.cnt_trx_abonostot_12m,
    a.cnt_trx_cargostot_12m,
    a.max_trx_abonos_1m,
    a.imp_trx_abonostot_3m,
    a.imp_trx_abonostot_9m,
    a.imp_trx_abonosefect_12m,
    a.cnt_meses_siningresos_12m,
    a.cnt_meses_sinegresos_12m,
    a.mto_pas_soles,
    -- ROS
    a.cnt_ros_hist,
    a.flg_ros_12m,
    -- Estructuración
    a.mto_ro_debajo_umbral,
    a.cnt_ro_debajo_umbral,
    a.imp_trx_debajo10k_ing_12m,
    a.cnt_trx_debajo10k_ing_12m,
    a.imp_trx_debajo10k_egr_12m,
    a.cnt_trx_debajo10k_egr_12m,
    -- Exterior
    a.flg_al_ext_12m,
    a.flg_del_ext_12m,
    a.mto_al_ext_12m,
    a.mto_del_ext_12m,
    a.mto_ing_delextrsgalto_12m,
    a.mto_al_extrsgaltot_12m,
    a.rat_ing_dl_xt_lt_tot_12m,
    a.rat_mto_al_xt_lt_12m,
    -- PEP y listas de riesgo
    a.flg_pep,
    a.cod_rsg_pep,
    a.cod_v01_lista_rsg,
    a.mto_cp_pep_ing,
    a.mto_cp_pep_egr,
    -- Contraparte con riesgo
    a.flg_t1cp_rosing_12m,
    a.flg_cp_ros_egr_12m,
    a.mto_cp_tot_ing_ros,
    a.mto_cp_tot_egr_ros,
    -- Riesgo geográfico y de canal
    a.cod_v12_lugar_rsdn_rsg,
    a.cod_v13_lugar_op_rsg_12m,
    a.cod_v11_pais_op_rsg,
    a.cod_v16_canal_op_rsg_12m,
    -- Tiendas y canales de alto riesgo
    a.mto_ing_tnda_rsg_alto_12m,
    a.cnt_tienda_rsg_alto_12m,
    a.mto_ing_cnl_rsg_alto_12m,
    a.cnt_canal_rsg_alto_12m,
    -- Historial de alertas y variación de efectivo
    a.flg_alerta_12m,
    a.cnt_alerta_hist,
    a.flg_vrcn_efe_cargos_5m_1m,
    a.mto_dif_abn_crgsefe_6m,
    a.rat_trx_mntabnsefetot_6m,
    a.rat_mntcrgsefetot_6m,
    -- Captaciones (t) — lag-1 externo vía JOIN a e_perm_aws
    COALESCE(t.concentracion_dia_max, 0)                                    AS concentracion_dia_max,
    COALESCE(t.monto_debitos_soles, 0)                                      AS monto_debitos_soles,
    COALESCE(t.monto_efectivo_soles, 0)                                     AS monto_efectivo_soles,
    COALESCE(t.monto_max_soles, 0)                                          AS monto_max_soles,
    COALESCE(t.monto_promedio_dolares, 0)                                   AS monto_promedio_dolares,
    COALESCE(t.monto_std_soles, 0)                                          AS monto_std_soles,
    COALESCE(t.monto_total_dolares, 0)                                      AS monto_total_dolares,
    COALESCE(t.monto_transferencias_soles, 0)                               AS monto_transferencias_soles,
    COALESCE(t.n_canales_distintos, 0)                                      AS n_canales_distintos,
    COALESCE(t.n_consumos, 0)                                               AS n_consumos,
    COALESCE(t.n_cuentas_distintas, 0)                                      AS n_cuentas_distintas,
    COALESCE(t.n_trx_app, 0)                                                AS n_trx_app,
    COALESCE(t.n_trx_efectivo, 0)                                           AS n_trx_efectivo,
    COALESCE(t.n_trx_mismo_cliente, 0)                                      AS n_trx_mismo_cliente,
    COALESCE(t.n_trx_otros, 0)                                              AS n_trx_otros,
    COALESCE(t.n_trx_pagos, 0)                                              AS n_trx_pagos,
    COALESCE(t.ratio_debito_credito, 0)                                     AS ratio_debito_credito,
    -- Tarjeta de crédito (c) — lag-1 externo vía JOIN a e_perm_aws
    COALESCE(c.tc_total_monto_mes, 0)                                       AS tc_total_monto_mes,
    COALESCE(c.tc_std_monto_mes, 0)                                         AS tc_std_monto_mes,
    COALESCE(c.tc_pct_no_autorizadas, 0)                                    AS tc_pct_no_autorizadas,
    -- Tarjeta de débito (d) — lag-1 externo vía JOIN a e_perm_aws
    COALESCE(d.td_avg_monto_1h, 0)                                          AS td_avg_monto_1h,
    COALESCE(d.td_monto_total, 0)                                           AS td_monto_total,
    COALESCE(d.td_gap_promedio, 0)                                          AS td_gap_promedio,
    -- Feature engineering (eps=0.01)
    COALESCE(c.tc_total_monto_mes, 0) + COALESCE(d.td_monto_total, 0) + COALESCE(t.monto_total_soles, 0)
                                                                            AS fe_monto_total_combinado,
    (
        COALESCE(t.n_trx_madrugada, 0) + COALESCE(t.n_trx_noche, 0)
    ) / (COALESCE(t.n_trx_mes, 0) + 1.0)                                   AS fe_pct_trx_fuera_horario,
    COALESCE(t.monto_efectivo_soles, 0)
        / (COALESCE(t.monto_total_soles, 0) + 0.01)                        AS fe_ratio_efectivo_vs_total,
    COALESCE(t.monto_debitos_soles, 0)
        / (COALESCE(t.monto_creditos_soles, 0) + 0.01)                     AS fe_ratio_salidas_entradas,
    COALESCE(t.monto_transferencias_soles, 0)
        / (COALESCE(t.monto_total_soles, 0) + 0.01)                        AS fe_ratio_transferencias_vs_total,
    COALESCE(t.monto_debitos_soles, 0)
        / (COALESCE(v.saldo_prom_tot_pasivo, 0) + 0.01)                    AS fe_velocidad_rotacion,
    (
        COALESCE(a.imp_trx_abonostot_1m, 0) - COALESCE(a.imp_trx_abonostot_6m, 0) / 6.0
    ) / (
        ABS(COALESCE(a.imp_trx_abonostot_1m, 0) - COALESCE(a.imp_trx_abonostot_6m, 0) / 6.0) + 0.01
    )                                                                       AS fe_zscore_abonos,
    (
        COALESCE(a.imp_trx_cargostot_1m, 0) - COALESCE(a.imp_trx_cargostot_6m, 0) / 6.0
    ) / (
        ABS(COALESCE(a.imp_trx_cargostot_1m, 0) - COALESCE(a.imp_trx_cargostot_6m, 0) / 6.0) + 0.01
    )                                                                       AS fe_zscore_cargos,
    -- Feature engineering — nuevas variables PLAFT
    -- fe_ros_por_antiguedad: densidad histórica de ROS relativa a la antigüedad del cliente
    COALESCE(a.cnt_ros_hist, 0)
        / (COALESCE(a.num_antiguedad, 0) + 1.0)                            AS fe_ros_por_antiguedad,
    -- fe_estructuracion_ratio: fracción de operaciones bajo umbral de reporte sobre el total
    (COALESCE(a.cnt_trx_debajo10k_ing_12m, 0) + COALESCE(a.cnt_trx_debajo10k_egr_12m, 0))
        / (COALESCE(a.cnt_trx_abonostot_12m, 0) + COALESCE(a.cnt_trx_cargostot_12m, 0) + 1.0)
                                                                            AS fe_estructuracion_ratio,
    -- fe_exterior_vs_pasivo: volumen total exterior (ingresos + egresos) relativo al saldo pasivo
    (COALESCE(a.mto_del_ext_12m, 0) + COALESCE(a.mto_al_ext_12m, 0))
        / (COALESCE(a.mto_pas_soles, 0) + 0.01)                           AS fe_exterior_vs_pasivo,
    -- fe_pep_exposure: exposición total a contrapartes PEP relativa al saldo pasivo
    (COALESCE(a.mto_cp_pep_ing, 0) + COALESCE(a.mto_cp_pep_egr, 0))
        / (COALESCE(a.mto_pas_soles, 0) + 0.01)                           AS fe_pep_exposure,
        a.cod_mes as periodo

FROM alarmas a
-- e_perm_aws.* no tienen features pre-calculadas → lag-1 externo vía DATE_ADD.
LEFT JOIN features_credito c
    ON  a.cuc_num = c.cuc_num
    AND DATE_ADD('month', -1, a.mes) = c.mes
LEFT JOIN features_debito d
    ON  a.cuc_num = d.cuc_num
    AND DATE_ADD('month', -1, a.mes) = d.mes
LEFT JOIN trx_agregadas t
    ON  a.cuc_num = t.cuc_num
    AND DATE_ADD('month', -1, a.mes) = t.mes
LEFT JOIN v360_reducido v
    ON  a.cuc_num = LPAD(CAST(v.cuc AS VARCHAR), 10, '0')
    AND DATE_FORMAT(DATE_ADD('month', -1, a.mes), '%Y%m') = v.codmes
