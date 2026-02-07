use anchor_lang::prelude::*;
use anchor_spl::token_interface::{Mint, TokenAccount, TokenInterface};
use anchor_spl::associated_token::AssociatedToken;

declare_id!("OBiPass111111111111111111111111111111111111");

#[program]
pub mod obi_pass {
    use super::*;

    // 1. Inicializar a "Casa da Moeda" (Mint Authority)
    pub fn initialize(ctx: Context<Initialize>) -> Result<()> {
        msg!("🚀 OBI Pass: Protocolo Inicializado!");
        Ok(())
    }

    // 2. Comprar Licença (Mint OBI Pass)
    // O usuário paga uma taxa (ex: 1 SOL ou 100 USDC) e recebe 1 Token 2022 (SBT ou NFT)
    pub fn mint_license(ctx: Context<MintLicense>) -> Result<()> {
        msg!("🎟️ Mintando OBI Pass para: {}", ctx.accounts.buyer.key());

        // TODO: Implementar transferência de pagamento (SOL/USDC) para o Treasury
        // system_program::transfer(...)

        // Mintar 1 Token para o comprador
        // Usando Token Extensions (Token 2022) para metadados on-chain
        anchor_spl::token_interface::mint_to(
            CpiContext::new_with_signer(
                ctx.accounts.token_program.to_account_info(),
                anchor_spl::token_interface::MintTo {
                    mint: ctx.accounts.mint.to_account_info(),
                    to: ctx.accounts.buyer_token_account.to_account_info(),
                    authority: ctx.accounts.mint_authority.to_account_info(),
                },
                &[], // Seeds para PDA se necessário
            ),
            1, // Quantidade: 1 Licença
        )?;

        msg!("✅ Licença emitida com sucesso!");
        Ok(())
    }
}

#[derive(Accounts)]
pub struct Initialize<'info> {
    #[account(mut)]
    pub payer: Signer<'info>,
    
    #[account(
        init,
        payer = payer,
        mint::decimals = 0,
        mint::authority = mint_authority,
        mint::freeze_authority = mint_authority,
    )]
    pub mint: InterfaceAccount<'info, Mint>, // Token 2022 Mint
    
    /// CHECK: PDA Authority
    #[account(seeds = [b"authority"], bump)]
    pub mint_authority: UncheckedAccount<'info>,
    
    pub system_program: Program<'info, System>,
    pub token_program: Interface<'info, TokenInterface>, // Token 2022
}

#[derive(Accounts)]
pub struct MintLicense<'info> {
    #[account(mut)]
    pub buyer: Signer<'info>,
    
    #[account(mut)]
    pub mint: InterfaceAccount<'info, Mint>,
    
    /// CHECK: PDA Authority que assina o mint
    #[account(seeds = [b"authority"], bump)]
    pub mint_authority: UncheckedAccount<'info>,
    
    #[account(
        init_if_needed,
        payer = buyer,
        associated_token::mint = mint,
        associated_token::authority = buyer,
    )]
    pub buyer_token_account: InterfaceAccount<'info, TokenAccount>,
    
    pub system_program: Program<'info, System>,
    pub token_program: Interface<'info, TokenInterface>,
    pub associated_token_program: Program<'info, AssociatedToken>,
    pub rent: Sysvar<'info, Rent>,
}
