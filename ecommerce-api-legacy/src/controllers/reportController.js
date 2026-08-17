'use strict';

const makeReportController = ({ reportService }) => ({
    async financial(req, res) {
        const report = await reportService.financialReport();
        return res.status(200).json(report);
    },
});

module.exports = { makeReportController };
