// timestamp for confirmation
var CONFIRMATION_TIMESTAMP = "";

/**
 * Delete a Paste by ID
 *
 * @param {string} id
 */
function deletePaste(id) {
  $.post('../../func/paste.php', {delete_id: id})
          .done(function(response) {
              $('#paste-card-' + id).remove();
              if($('#paste-list').children().length <= 0) {
                $('#paste-list').html("<h3 class='no-pastes'>No Pastes found!</h3>");
              }
          })
          .fail(function(xhr, status, error) {
              showError("Paste deletion failed", id);
          });
}

/**
 * Make Network-Time-Protocol
 * API-Call
 */
function callNTP() {
  $.get('../../func/ntp.php', function(response) {
    CONFIRMATION_TIMESTAMP = response.trim(); //replace(/\ /gm, "");
    $('#timestamp').html(CONFIRMATION_TIMESTAMP);
  });
}

/**
 * Purge all Pastes
 */
function purgeAllPastes() {
  let entered_timestamp = $('#entered_timestamp').val().toString();
  if(entered_timestamp === CONFIRMATION_TIMESTAMP) {
    Array.prototype.forEach.call($('#paste-list').children(), async function(child) {
      let child_id = $(child).attr("id").split("-").slice(-1)[0];
      await deletePaste(child_id);
    });
    showSuccess("Purge was successful", "confirmation");
    $('#confirm_purge, #finish_purge, #cancel_purge').toggleClass("hidden");
  } else {
    showError("Wrong confirmation code entered", "confirmation");
  }
}